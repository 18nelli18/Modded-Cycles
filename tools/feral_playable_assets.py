"""Formula Feral : demarrage audible, seize formules conservees (note147).
Etat prive dans l'union Formula (+8/+12 apres temps/phase), sans RAM globale.
Entree de fonction : d0/d1/a0/a1 volatils, trampoline rejoue le prologue entier.
"""
import struct,subprocess
CODE=0x467ee000;END=0x467ef000
SEED=1234567
ASM=r'''.text
.globl feral_formula_entry,feral_formula_reset
feral_formula_entry:
 movea.l 4(%sp),%a0
 movea.l 8(%sp),%a1
 move.l 20(%a1),%d0
 moveq #11,%d1
 asr.l %d1,%d0
 move.l #0x46524d31,%d1
 cmp.l 12(%a0),%d1
 bne.s 1f
 cmp.l 8(%a0),%d0
 beq.s 2f
1: move.l %d0,8(%a0)
 move.l %d1,12(%a0)
 moveq #1,%d0
 move.l %d0,68(%a1)
2:
 lea -100(%sp),%sp
 movem.l %d2-%d7/%a2-%a6,(%sp)
 jmp 0x467d541a
feral_formula_reset:
 move.l 20(%a5),%d0
 moveq #11,%d1
 asr.l %d1,%d0
 cmpi.l #10,%d0
 beq.s 1f
 move.l #1234567,%d0
 bra.s 2f
1: moveq #0,%d0
2: move.l %d0,(%a0)
 clr.l 4(%a0)
 moveq #0,%d1
 jmp 0x467d5430
'''
def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import TAIL
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 src=build/'feral_playable.S';obj=src.with_suffix('.o');elf=src.with_suffix('.elf');binary=src.with_suffix('.bin');src.write_text(ASM)
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(src),'-o',str(obj)],check=True)
 subprocess.run([cross+'ld.exe','-e','feral_formula_entry','-Ttext',hex(CODE),'-o',str(elf),str(obj)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};blob=binary.read_bytes();assert CODE+len(blob)<END
 assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]);patch(CODE,bytes(len(blob)),blob,tail)
 for at,expected,label in [(0x467d5412,'4fefff9c48d77cfc','feral_formula_entry'),(0x467d569c,'42a80004429042804281','feral_formula_reset')]:
  old=bytes.fromhex(expected);assert len(old)>=6 and len(old)%2==0
  patch(at,old,b'\x4e\xf9'+struct.pack('>I',sy[label])+b'\x4e\x71'*((len(old)-6)//2),tail)
 return dict(code=CODE,code_bytes=len(blob),symbols=sy,seed=SEED,formula10_seed=0,models_retained=10,formulas_retained=16,formula_restarts_on_color_group_change=True,hardware_tested=False,status='experimental')
