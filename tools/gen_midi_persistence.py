#!/usr/bin/env python3
"""Note 98 : extension MPI1 relogeable pour Banque RAM actuelle, experimentale.

python3 tools/gen_midi_persistence.py [--check] [--output fichier.js]
Aucun octet officiel n'est inclus ; les API sont reliees a la recette au build.
"""
import argparse,json,pathlib,re,shutil,subprocess,tempfile
from gen_seq_gen import symbols
ROOT=pathlib.Path(__file__).resolve().parents[1]
API=['ml_context','ml_bank_table','ml_bank_empty','ml_pattern','ml_play_pattern',
 'ml_repeat_pattern_lookup','ml_repeat_pattern_prepare','ml_repeat_project_reset',
 'ml_repeat_reset_pending','mlkc_locks_for','mlkc_locks_reset','mlkc_state',
 'mlcc_settings','mlcc_prepare','mlcc_refresh','ml_bank_ui_sync','mlp_clip_invalidate',
 'ml_ui_drain','TG_show_popup','ml_active_pattern_id','ml_runtime','ml_clock_state',
 'ml_bank_activate','mlkc_assign_cancel','OLD_LOAD','ml_gq_state','ml_gu_valid',
 'SG_undo_valid','mlp_held','mlp_remove','mlp_changed','mlcc_cfg_init','mlcc_context']
def generate():
    cross=next((c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'gcc')),'m68k-linux-gnu-')
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d);src=ROOT/'tools/machines/midi_lanes'
        subprocess.run([cross+'gcc','-std=gnu99','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-fno-pic','-fno-stack-protector','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src/'persistence.c'),'-o',str(p/'c.o')],check=True)
        subprocess.run([cross+'gcc','-mcpu=54418','-c',str(src/'persistence_hooks.s'),'-o',str(p/'s.o')],check=True)
        (p/'link.ld').write_text('SECTIONS { .text 0 : { *(.text*) *(.rodata*) } . = ALIGN(4); .data : { *(.data*) } . = ALIGN(4); .bss : { *(.bss*) *(COMMON) } . = ALIGN(4); mp_end = .; }')
        subprocess.run([cross+'ld','--emit-relocs','-T',str(p/'link.ld'),'-o',str(p/'e.elf'),str(p/'c.o'),str(p/'s.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'e.elf'),str(p/'e.bin')],check=True)
        s=symbols(cross,p/'e.elf');body=(p/'e.bin').read_bytes();body+=bytes(s['mp_end']-len(body))
        rel=subprocess.check_output([cross+'readelf','-rW',str(p/'e.elf')],text=True)
        offsets=[int(m.group(1),16) for m in re.finditer(r'^([0-9a-f]+)\s+\S+\s+R_68K_32\b',rel,re.M)]
        for off in offsets:assert int.from_bytes(body[off:off+4],'big')<len(body)
        data={'hex':body.hex(),'symbols':s,'reloc':offsets,'api':API,'status':'experimental','record_bytes':14304}
        return '// Genere par tools/gen_midi_persistence.py ; code propre uniquement.\nwindow.MCMidiPersistence='+json.dumps(data,separators=(',',':'))+';\n'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default='docs/flasher-midi-save-current-test/midi-persistence-data.js');p.add_argument('--check',action='store_true');a=p.parse_args()
    out=ROOT/a.output;text=generate()
    if a.check:assert out.read_text(encoding='utf-8')==text
    else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding='utf-8')
    print('ok extension MPI1 experimentale, relocations ELF et ABI courante')
if __name__=='__main__':main()
