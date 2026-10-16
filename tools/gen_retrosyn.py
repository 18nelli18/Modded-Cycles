#!/usr/bin/env python3
"""Machine RETROSYN OS 1.13 : generateur experimental (notes/96).

Reutilise les detours et le contrat de MACRO ; aucun octet Elektron fourni.
python3 tools/gen_retrosyn.py --cycles firmware/model-cycles_OS1.13.syx [--check]
"""
import argparse
import hashlib
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))
import gen_macro as gm
import gen_syntakt_engines as gs
import gen_sdvintage_7th as g7
import build

SRC = HERE / "machines" / "retrosyn"
DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
MACHINE = dict(name="RETROSYN", image=4, decay=50,
               knobs=(("Color", "COLR", 0), ("Shape", "SHAP", 0, 0, 5),
                      ("Sweep", "SWEP", 64), ("Contour", "CONT", 0)))


def compile_machine(tmp, repo, pay, bss_at=None):
    """Code entier ColdFire, tables en lecture seule ; six etats en BSS."""
    obj, elf, binary, ld = [tmp / n for n in ("retrosyn.o", "retrosyn.elf", "retrosyn.bin", "link.ld")]
    gm.gx.run([gm.gx.CROSS + "gcc", *gm.gx.CFLAGS, "-std=c99", "-c", str(SRC / "retrosyn.c"), "-o", str(obj)])
    script = gm.LINK.format(code=pay, bss=bss_at or pay + gm.BSS_OFF).replace("macro_update", "retrosyn_update").replace("macro_render", "retrosyn_render")
    ld.write_text(script.replace("*(COMMON)", "*(COMMON) . = ALIGN(4); retrosyn_bss_end = .;"))
    gm.gx.run([gm.gx.CROSS + "ld", "-T", str(ld), "--gc-sections", "-e", "retrosyn_update", "-u", "retrosyn_render", "-o", str(elf), str(obj)])
    gm.gx.run([gm.gx.CROSS + "objcopy", "-O", "binary", "-R", ".bss", str(elf), str(binary)])
    syms = {p[2]: int(p[0], 16) for line in gm.gx.run([gm.gx.CROSS + "nm", str(elf)]).splitlines()
            if len(p := line.split()) == 3}
    blob = binary.read_bytes()
    if pay + len(blob) > pay + gs.LAYOUT["STUBS"]:
        raise SystemExit("!! RETROSYN depasse ses detours")
    end = syms["retrosyn_bss_end"]
    syms.update(macro_update=syms["retrosyn_update"], macro_render=syms["retrosyn_render"])
    return blob, syms, end


def generate(stock, sampler=None):
    engine = dict(machine=MACHINE, compile=compile_machine, symbols=("retrosyn_update", "retrosyn_render", "tracks"))
    context=None
    if sampler:
        ap=sampler['append'];current,_=build.apply_writes(stock,[sampler])
        context={k:int(v,16) for k,v in sampler['symbols'].items()}
        context.update(img=current,blob=bytes.fromhex(ap['parts'][0]['hex']),blob_at=int(ap['dest'],16),
                       at=int(ap['at'],16)+ap['size'],id='sample-wizard')
    t, info = gm.build_tweak(stock, None, tg=context, engine=engine)
    t.update(id="retrosyn-wizard" if sampler else "retrosyn", order=37 if sampler else 27,
             status="experimental", name="Machine RETROSYN : six oscillateurs retro",
             description=["PULSE, TRI, WAVE, NOISE-L, NOISE-S, SNES ; COLOR : rapport/table/cadence ; SWEEP : hauteur ; CONTOUR : arpege.",
                          "DECAY et GATE : enveloppe TONE ; FINE : accord fin ; PUNCH : quantification quatre bits.",
                          "Niveau et charge six pistes a verifier sur machine. tools/gen_retrosyn.py ; notes/96."])
    # Tous les autres ajouts prennent les memes tables et le meme crochet.
    t["conflicts"] = sorted({p["id"] for f in DEV.glob("*.json")
                             if f.name != "device.json" and "append" in (p := json.loads(f.read_text()))
                             and p["id"] not in {t["id"], 'sample-wizard' if sampler else ''}} | gm.other_ids())
    build.apply_writes(stock, ([sampler] if sampler else [])+[t])
    if sampler:t['sampler_recipe']=sampler
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--output", type=pathlib.Path)
    ap.add_argument("--wizard-catalog", type=pathlib.Path)
    a = ap.parse_args()
    device = json.loads((DEV / "device.json").read_text())
    if hashlib.sha256(pathlib.Path(a.cycles).read_bytes()).hexdigest() != device["stock_syx_sha256"]:
        raise SystemExit("!! OS officiel 1.13 attendu")
    stock = g7.cycles_main(a.cycles)
    sampler=json.loads(a.wizard_catalog.read_text())['variants']['0']['wizard'] if a.wizard_catalog else None
    if sampler:
        allowed={'sample-wizard','retrosyn-wizard','retrosyn-all-machines-wizard'}
        conflicts=set(sampler.get('conflicts',[]))
        for f in DEV.glob('*.json'):
            if f.name=='device.json':continue
            other=json.loads(f.read_text())
            if other['id'] in allowed:continue
            overlap=any(x['off']<y['off']+len(y['new'])//2 and y['off']<x['off']+len(x['new'])//2
                        and x!=y for x in sampler['writes'] for y in other.get('writes',[]))
            if 'append' in other or overlap:conflicts.add(other['id'])
        sampler['conflicts']=sorted(conflicts)
        sample_text=json.dumps(sampler,indent=1,ensure_ascii=False)+'\n'
        sample_path=DEV/'20-sample-wizard.json'
        if a.check:
            if not sample_path.exists() or sample_path.read_text()!=sample_text:raise SystemExit(f'FAIL {sample_path}')
        else:sample_path.write_text(sample_text,encoding='utf-8')
    t = generate(stock,sampler)
    out = a.output or DEV / ("37-retrosyn-wizard.json" if sampler else "27-retrosyn.json")
    text = json.dumps(t, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        if not out.exists() or out.read_text() != text:
            raise SystemExit(f"FAIL {out}")
    else:
        out.write_text(text, encoding="utf-8")
    print("ok", t["id"], out)

if __name__ == "__main__":
    main()
