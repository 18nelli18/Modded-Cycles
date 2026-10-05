// Posts project news to the Modded Cycles Discord server through channel webhooks.
//
//   node .github/scripts/discord.mjs release <before-sha> <after-sha>
//     A new version at the top of docs/assets/release.js -> #announcements (pings the "Release pings" role).
//     A mod that becomes experimental or tested in docs/flasher/tweaks.js -> #dev-updates (pings "Tester"
//     for a new experimental mod).
//   node .github/scripts/discord.mjs pr
//     A pull request merged into main (event payload in GITHUB_EVENT_PATH) -> #dev-updates.
//
// Webhook URLs come from DISCORD_WEBHOOK_ANNOUNCEMENTS and DISCORD_WEBHOOK_DEV_UPDATES (repository secrets).
// A missing secret skips that post. DRY_RUN=1 prints the payloads instead of sending them.

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const SITE = "https://18nelli18.github.io/Modded-Cycles/";
const ROLE_RELEASES = process.env.DISCORD_ROLE_RELEASES || "";
const ROLE_TESTERS = process.env.DISCORD_ROLE_TESTERS || "";
const CHANNEL_TEST_REPORTS = process.env.DISCORD_CHANNEL_TEST_REPORTS || "";
const DRY = process.env.DRY_RUN === "1";

function fileAt(sha, path) {
  if (!sha || /^0+$/.test(sha)) return null;
  try {
    return execFileSync("git", ["show", `${sha}:${path}`], { encoding: "utf8", maxBuffer: 64 << 20 });
  } catch {
    return null;
  }
}

function evalWindow(src, key) {
  if (!src) return null;
  const ctx = { window: {} };
  vm.runInNewContext(src, ctx);
  return ctx.window[key] ?? null;
}

// English card label of a mod, from FEAT.en in docs/flasher/app.js (first occurrence is the en block).
function labelOf(id, appSrc) {
  const key = id.replace(/[.*+?^${}()|[\]\\-]/g, "\\$&");
  const m = appSrc && appSrc.match(new RegExp(`\\n\\s*"?${key}"?: \\{ label: "([^"]+)"`));
  return m ? m[1] : id;
}

const clip = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);
const mention = (role) => (role ? `<@&${role}> ` : "");

async function post(url, payload, what) {
  if (DRY) {
    console.log(`[dry run] ${what}\n${JSON.stringify(payload, null, 2)}`);
    return;
  }
  if (!url) {
    console.log(`skip ${what}: webhook secret not set`);
    return;
  }
  const res = await fetch(`${url}?wait=true`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`${what}: Discord answered ${res.status} ${await res.text()}`);
  console.log(`posted ${what}`);
}

async function releases(before, after) {
  const RELEASE = "docs/assets/release.js";
  const TWEAKS = "docs/flasher/tweaks.js";
  const oldRel = evalWindow(fileAt(before, RELEASE), "MC_RELEASES") || [];
  const newRel = evalWindow(fileAt(after, RELEASE), "MC_RELEASES") || [];
  const known = new Set(oldRel.map((r) => r.version));
  // Nothing to compare against (first push of a branch): never flood the channel with the whole history.
  const fresh = oldRel.length ? newRel.filter((r) => !known.has(r.version)).reverse() : [];

  for (const r of fresh) {
    const lines = r.changes.map((c) => `• ${c.en}`);
    await post(process.env.DISCORD_WEBHOOK_ANNOUNCEMENTS, {
      content: `${mention(ROLE_RELEASES)}**Modded Cycles ${r.version}** is out.`,
      allowed_mentions: { roles: ROLE_RELEASES ? [ROLE_RELEASES] : [] },
      embeds: [{
        title: `Modded Cycles ${r.version}`,
        url: `${SITE}#version`,
        description: clip(lines.join("\n\n"), 3600) +
          `\n\n🌐 [Open the flasher](${SITE}flasher/) · 📖 [Guide](${SITE}guide/) · 🇫🇷 [Notes en français](${SITE}#version)`,
        color: 0xff6a13,
        footer: { text: `Released ${r.date}` },
      }],
    }, `release ${r.version}`);
  }

  const oldF = (evalWindow(fileAt(before, TWEAKS), "MC_TWEAKS") || {}).features;
  const newF = (evalWindow(fileAt(after, TWEAKS), "MC_TWEAKS") || {}).features || [];
  if (!oldF) return;
  const was = new Map(oldF.map((f) => [f.id, f.status]));
  const app = fileAt(after, "docs/flasher/app.js");
  for (const f of newF) {
    if (was.get(f.id) === f.status) continue;
    const name = labelOf(f.id, app);
    if (f.status === "experimental") {
      const where = CHANNEL_TEST_REPORTS ? `<#${CHANNEL_TEST_REPORTS}>` : "#test-reports";
      await post(process.env.DISCORD_WEBHOOK_DEV_UPDATES, {
        content: `${mention(ROLE_TESTERS)}🧪 **New experimental mod: ${name}.** It is in the flasher now. ` +
          `It passed the emulator and still needs testing on real machines: if you try it, tell us how it went in ${where}.\n` +
          `📖 <${SITE}guide/>`,
        allowed_mentions: { roles: ROLE_TESTERS ? [ROLE_TESTERS] : [] },
      }, `experimental ${f.id}`);
    } else if (f.status === "tested") {
      await post(process.env.DISCORD_WEBHOOK_DEV_UPDATES, {
        content: `✅ **${name}** is now marked Tested: it has run on a real Model:Cycles. Thanks to everyone who reported!`,
        allowed_mentions: { parse: [] },
      }, `tested ${f.id}`);
    }
  }
}

async function mergedPr() {
  const ev = JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH, "utf8"));
  const pr = ev.pull_request;
  if (!pr || !pr.merged) return;
  await post(process.env.DISCORD_WEBHOOK_DEV_UPDATES, {
    allowed_mentions: { parse: [] },
    embeds: [{
      title: clip(`🔀 ${pr.title}`, 250),
      url: pr.html_url,
      description: `Merged into \`${pr.base.ref}\` · #${pr.number} by ${pr.user.login}`,
      color: 0x3498db,
    }],
  }, `merged PR #${pr.number}`);
}

const [mode, before, after] = process.argv.slice(2);
if (mode === "release") await releases(before, after || "HEAD");
else if (mode === "pr") await mergedPr();
else {
  console.error("usage: discord.mjs release <before> <after> | pr");
  process.exit(2);
}
