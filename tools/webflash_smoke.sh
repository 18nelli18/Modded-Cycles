#!/usr/bin/env bash
# Browser smoke test of the web flasher (docs/flasher/) with jsdom: loads the real
# page and its scripts, fakes Web MIDI, and walks through the 4 steps (choose, OS file,
# connect, flash, stop). Checks there is NO JS error, that each step says what is
# missing, and that building then sending works.
#
#   tools/webflash_smoke.sh                               # synthetic OS only
#   tools/webflash_smoke.sh model-cycles_OS1.13.syx       # + the 5 real builds vs their reference hashes
#
# jsdom is installed in a temporary folder (npm): nothing is added to the repository.
# Needs node, npm and network access (registry.npmjs.org).
set -euo pipefail
cd "$(dirname "$0")/.."
command -v node >/dev/null || { echo "node is required"; exit 1; }
command -v npm >/dev/null || { echo "npm is required"; exit 1; }
REAL_OS="${1:-}"
if [ -n "$REAL_OS" ]; then REAL_OS="$(cd "$(dirname "$REAL_OS")" && pwd)/$(basename "$REAL_OS")"; fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

python3 tools/webbuild_synth.py "$tmp" >/dev/null       # makes synth.syx + meta.json
( cd "$tmp" && npm init -y >/dev/null 2>&1 && npm install jsdom >/dev/null 2>&1 )
NODE_PATH="$tmp/node_modules" node tools/webflash_smoke.js "$tmp" $REAL_OS
