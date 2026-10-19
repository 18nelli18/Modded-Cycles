"""Menu Pad Setup USB 2/6 : compile le helper et ses tables depuis le patch 6ch-usbup.

Le firmware de base reste en 6 canaux. L'utilisateur peut basculer en 2 canaux dans Pad Setup ;
le pilote USB repasse par le mode MIDI seul pour forcer la re-enumeration de l'hote.
Genere docs/flasher/pad-mode-data.js depuis les sources partagees avec le menu Silent/Stock.
"""
import argparse
import json
import pathlib
import re
import subprocess
import tempfile

import gen_macro as gm

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = 0x40000400


def symbols(cross, elf):
    result = {}
    for row in subprocess.check_output([cross + "nm", str(elf)], text=True).splitlines():
        parts = row.split()
        if len(parts) == 3:
            result[parts[2]] = int(parts[0], 16)
    return result


def usb_patches():
    tweak = json.loads((ROOT / "tweaks/model-cycles_OS1.13/11-6ch-usbup.json").read_text())
    patches = []
    for write in tweak["writes"]:
        at = write["off"] + BASE
        if at < 0x40003000 or at >= 0x4019B000:
            if isinstance(write["old"], str) and isinstance(write["new"], str):
                patches.append({"at": at, "two": write["old"], "six": write["new"]})
    if len(patches) != 15:
        raise SystemExit(f"USB mode: 15 plages attendues, {len(patches)} trouvees")
    return patches


def generate():
    patches = usb_patches()
    c = (ROOT / "tools/machines/wizard_control/control.c").read_text(encoding="utf-8")
    c = c.replace("u32 wf_menu_row(void){return 0;}", "static u32 row;\nu32 wf_menu_row(void){return row;}\nu32 uf_set(u32);")
    old = "if(editing){i32 delta=((i32 (*)(const u32 *,u32,u32))0x4006f73a)(event,1,1);if(delta)wf_stock=delta>0;repaint();}"
    new = "i32 delta=((i32 (*)(const u32 *,u32,u32))0x4006f73a)(event,1,1);if(delta){if(!editing)row=delta>0;else if(row)uf_set(delta>0);else wf_stock=delta>0;repaint();}"
    if old not in c:
        raise SystemExit("USB mode: controleur Pad Setup inattendu")
    c = c.replace(old, new)
    c += '\nvolatile u32 uf_six __attribute__((section(".data")))=1;\nvolatile u32 uf_popup __attribute__((section(".data")))=0;\n'
    tables = []
    for i, patch in enumerate(patches):
        for key in ("two", "six"):
            c += "static const u8 uf_" + key + str(i) + "[]={" + ",".join(str(v) for v in bytes.fromhex(patch[key])) + "};\n"
        tables.append("{" + hex(patch["at"]) + "," + str(len(patch["six"]) // 2) + ",uf_two" + str(i) + ",uf_six" + str(i) + "}")
    c += "struct uf_patch{u32 at,size;const u8 *two,*six;};\nstatic const struct uf_patch uf_patches[]={" + ",".join(tables) + "};\n"
    c += r'''
static u32 uf_guard(void){for(u32 i=0;i<sizeof(uf_patches)/sizeof(uf_patches[0]);i++){const struct uf_patch *p=uf_patches+i;const u8 *src=uf_six?p->six:p->two;for(u32 j=0;j<p->size;j++)if(((volatile u8*)p->at)[j]!=src[j])return 0;}return 1;}
extern void uf_push(u32);
void uf_copy(u32 six){for(u32 i=0;i<sizeof(uf_patches)/sizeof(uf_patches[0]);i++){const struct uf_patch *p=uf_patches+i;const u8 *src=six?p->six:p->two;for(u32 j=0;j<p->size;j++)((volatile u8*)p->at)[j]=src[j];for(u32 line=p->at&~15u;line<p->at+p->size;line+=16)uf_push(line);}uf_six=six;}
extern void uf_atomic(u32);
static void uf_notice(const char *text){if(uf_popup)((void(*)(const char*))uf_popup)(text);}
u32 uf_set(u32 six){
 six=!!six;if(six==uf_six)return 1;
 if(*(volatile u32*)0x40a7883c){uf_notice("Stop playback first");return 0;}
 u32 mode=((u32(*)(void))0x40004e38)();
 if(mode!=2&&mode!=5){uf_notice("USB busy");return 0;}
 if(!uf_guard()){uf_notice("USB code mismatch");return 0;}
 if(mode==5)((void(*)(u32))0x40004e04)(2);
 uf_atomic(six);
 if(mode==5)((void(*)(u32))0x40004e04)(5);
 uf_notice(six?"USB audio 6ch":"USB audio 2ch");return 1;
}
void uf_menu_value(u32 self,u32 item,u32 canvas,u32 x,u32 y){
 (void)self;(void)item;
 ((void (*)(u32,u32,u32,u32,u32,const char *,...))0x40071a04)(canvas,0x40ea14cc,x+24,y,4,"%s",uf_six?"6ch":"2ch");
 if(editing&&row)((void (*)(u32,u32,u32,u32,u32,u32))0x40070efc)(canvas,x-13,y-2,x+25,y+10,0xffffffffu);
}
'''
    c = c.replace("if(editing)((void", "if(editing&&!row)((void")
    menu = (ROOT / "tools/machines/wizard_control/menu.S").read_text(encoding="utf-8")
    menu = menu.replace("clrb %a0@(80)", "clrb %a0@(80)\n    clrb %a0@(164)")
    menu = menu.replace("moveq #1,%d0", "moveq #2,%d0").replace('.Loutput: .asciz "Out"', '.Loutput: .asciz "USB"')
    menu += '\n    .long 0,0,0,.Loutput,0,1,.Lts_label,0,0,0,0,0,0,1,uf_menu_value,0,0,0,0,0,0\n'
    hooks = (ROOT / "tools/machines/wizard_control/hooks.S").read_text(encoding="utf-8") + r'''
.text
.globl uf_push
uf_push:
 moveal %sp@(4),%a0
 cpushl %dc,(%a0)
 rts
.globl uf_atomic
uf_atomic:
 movel %d2,%sp@-
 clrl %d2
 movew %sr,%d2
 movew #0x2700,%sr
 movel %sp@(8),%sp@-
 jsr uf_copy
 addql #4,%sp
 nop
 movel #0xa40ce100,%d0
 movec %d0,%cacr
 nop
 movew %d2,%sr
 movel %sp@+,%d2
 rts
'''
    with tempfile.TemporaryDirectory() as folder:
        d = pathlib.Path(folder)
        objects = []
        for name, source in (("control.c", c), ("hooks.S", hooks), ("menu.S", menu)):
            path = ROOT / "build/usb-mode" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source.replace("uf_", "wf_usb_"), encoding="utf-8")
            obj = d / (name + ".o")
            gm.gx.run([gm.gx.CROSS + "gcc", *gm.gx.CFLAGS, "-DWF_PAD_ONLY=1", "-DWF_TAP_HOLD=1", "-fno-optimize-sibling-calls", "-std=c99", "-c", str(path), "-o", str(obj)])
            objects.append(str(obj))
        (d / "x.ld").write_text("SECTIONS { .text 0 : { *(.text*) *(.rodata*) } . = ALIGN(4); .data : { *(.data*) } . = ALIGN(4); .bss : { *(.bss*) *(COMMON) } . = ALIGN(4); wf_end = .; }")
        gm.gx.run([gm.gx.CROSS + "ld", "--emit-relocs", "-T", str(d / "x.ld"), "-o", str(d / "x.elf"), *objects])
        gm.gx.run([gm.gx.CROSS + "objcopy", "-O", "binary", str(d / "x.elf"), str(d / "x.bin")])
        sy = symbols(gm.gx.CROSS, d / "x.elf")
        raw = (d / "x.bin").read_bytes()
        raw += bytes(sy["wf_end"] - len(raw))
        rel = gm.gx.run([gm.gx.CROSS + "readelf", "-rW", str(d / "x.elf")])
        reloc = [int(m.group(1), 16) for m in re.finditer(r"^([0-9a-f]+)\s+\S+\s+R_68K_32\b", rel, re.M)]
        if not all(int.from_bytes(raw[i:i+4], "big") < len(raw) for i in reloc):
            raise SystemExit("USB mode: pointeur de relocalisation invalide")
    data = {"hex": raw.hex(), "symbols": sy, "reloc": reloc}
    out = ROOT / "docs/flasher/pad-mode-data.js"
    return data, out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data, out = generate()
    text = "window.MCPadMode=" + json.dumps(data, separators=(",", ":")) + ";\n"
    if args.check:
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            raise SystemExit("pad-mode-data.js n'est pas a jour")
    else:
        out.write_text(text, encoding="utf-8")
        build = ROOT / "build/usb-mode/data.json"
        build.write_text(json.dumps(data), encoding="utf-8")
    print("PASS menu Pad Setup USB 2/6 compile ; 15 plages pilote/descripteur")


if __name__ == "__main__":
    main()
