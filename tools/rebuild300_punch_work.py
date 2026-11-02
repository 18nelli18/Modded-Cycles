"""PUNCH : utiliser le masque existant pour supprimer trois tests redondants.

Un bit accepte garantit deja MACHINE6..24, PUNCH non nul et recette non vide.
La copie de frame ne change aucun de ces champs avant la seconde passe.
Le calcul de l'adresse de recette reste identique, ainsi que tout le DSP.
"""
import hashlib
import struct
import subprocess

CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'


def apply(meta,runtime,output):
    if not meta['activity_masks']['full']:return dict(excluded_by_edition=True,reason='Lite has no custom sound machines',code_bytes=0)
    entry=meta['activity_masks']['symbols']['pp_voice_loop'];base=0x46700000
    optional='rm_step' not in meta['per_track_fx']['symbols']
    prefix=bytes.fromhex('4a69000c6700' if optional else '4a68000c6700')
    offset=runtime.find(prefix,entry-base,entry-base+2048);assert offset>=0
    assert runtime.find(prefix,offset+1,entry-base+2048)<0
    length=30 if optional else 32
    old=bytes(runtime[offset:offset+length]);site=base+offset
    if optional:
        assert old[8:14]==bytes.fromhex('7e18be826500')
        calculation=old[16:22];assert calculation==bytes.fromhex('2e02e58fde82')
        assert old[22:28]==bytes.fromhex('4a3678026700')
    else:
        assert old[8:14]==bytes.fromhex('7c18bc836500')
        calculation=old[16:24];assert calculation==bytes.fromhex('2c03e58e2646d7c3')
        assert old[24:30]==bytes.fromhex('4a36b8026700')
    # Aucun saut ne doit entrer dans le milieu du bloc remplace.
    binary=output/'punch-original-runtime.bin';binary.write_bytes(runtime)
    text=subprocess.check_output([CROSS+'objdump.exe','-D','-b','binary','-m','m68k:isa-c:emac',f'--adjust-vma={base}',f'--start-address={entry}',f'--stop-address={entry+2048}',str(binary)],text=True)
    for line in text.splitlines():
        columns=line.split('\t')
        if len(columns)<3:continue
        instruction=columns[2].split()
        if len(instruction)<2 or not instruction[0].startswith(('b','j','db')):continue
        operand=instruction[1].removeprefix('0x')
        try:target=int(operand,16);pc=int(columns[0].strip().rstrip(':'),16)
        except ValueError:continue
        if not site<=pc<site+length:assert not site<target<site+length,('interior control entry',line)
    patch=calculation+b'\x60\x16'+b'\x4e\x71'*11
    assert len(patch)==length
    runtime[offset:offset+length]=patch
    return dict(code_bytes=0,patches=[dict(patch_site=site,patch_bytes=patch.hex(),old_entry_bytes=old.hex())],selection_mask_unchanged=True,stock_path_bytes_unchanged=True,no_new_state=True,no_added_dispatch=True,original_sha256=hashlib.sha256(old).hexdigest(),hardware_tested=False)
