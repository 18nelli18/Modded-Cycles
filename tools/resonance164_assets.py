"""196 : police native adaptee a Resonance, tous les autres labels exacts."""
import subprocess,struct
CODE=0x468f0000
def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import TAIL
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');obj=build/'resonance164.o';elf=obj.with_suffix('.elf');binary=obj.with_suffix('.bin');src=root/'tools/machines/resonance164/label.S'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(src),'-o',str(obj)],check=True)
 subprocess.run([cross+'ld.exe','-Ttext='+hex(CODE),'-e','rs_font','-o',str(elf),str(obj)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True);raw=binary.read_bytes();assert len(raw)<128
 assert TAIL+len(tail)<CODE;tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(raw)
 patch(0x4001e586,bytes.fromhex('487940ea14d4'),bytes.fromhex('4eb9')+struct.pack('>I',CODE),prefix)
 return dict(code=CODE,end=CODE+len(raw),label='Resonance',font='native small for Resonance only',audio_unchanged=True,status='experimental',hardware_tested=False)
