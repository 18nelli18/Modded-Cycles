"""Mix de sortie : omet les produits monitor nuls, ordre des sorties conserve.

Deux chemins specialises apres verification des coefficients ; le chemin
monitor actif rejoue les corps natifs, deroules quatre fois, sans nouvelle BSS.
"""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1];CODE=0x46799800;LIMIT=0x4679a400
def apply(meta,native,runtime,out):
 base=0x46700000;nb=0x40000400;out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert not any(runtime[CODE-base:LIMIT-base])
 assert any(x['kind']=='remove' and x['address']<=CODE and LIMIT<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
 bodies=[]
 for lo,hi,sha in [(0x40056bf6,0x40056c1a,'ba6dd8363ed33037584b01f55db020e576659287bf961a3eedbf42cdc2b768a8'),(0x40056c3e,0x40056c62,'437281f47460f01cfe322d14f8c22f4b0420b1945cb7f734c4d9733b50d08953')]:
  raw=bytes(native[lo-nb:hi-nb]);assert hashlib.sha256(raw).hexdigest()==sha;bodies.append('.byte '+','.join(map(str,raw))+'\n')
 asm='''.text
.globl om_first,om_second
om_first:
 move.l %a3,%d2
 or.l %d3,%d2
 bne.w .Lfirst_native
.Lfirst_zero:
 move.l 256(%a1),%a5
 mac.l %d1,%a5,(%a1)+,%a5,%acc0
 move.l 256(%a1),%a5
 mac.l %a4,%a5,(%a1)+,%a5,%acc1
 movclr.l %acc0,%d2
 move.l %d2,(%a0)+
 movclr.l %acc1,%d2
 move.l %d2,(%a0)+
 subq.l #1,%d4
 bgt.s .Lfirst_zero
 lea 128(%a2),%a2
 move.l (%a2),%a5
 jmp 0x40056c1e
.Lfirst_native:
.rept 4
'''+bodies[0]+'''.endr
 subq.l #4,%d4
 bgt.w .Lfirst_native
 jmp 0x40056c1e
.balign 4
om_second:
 move.l %d6,%d4
 or.l %d1,%d4
 bne.w .Lsecond_native
.Lsecond_zero:
 move.l 256(%a1),%d3
 mac.l %d7,%d3,(%a1)+,%d3,%acc0
 move.l 256(%a1),%d3
 mac.l %d2,%d3,(%a1)+,%d3,%acc1
 movclr.l %acc0,%d4
 move.l %d4,(%a0)+
 movclr.l %acc1,%d4
 move.l %d4,(%a0)+
 subq.l #1,%d0
 bgt.s .Lsecond_zero
 lea 128(%a2),%a2
 move.l (%a2),%d3
 tst.l %d0
 jmp 0x40056c66
.Lsecond_native:
.rept 4
'''+bodies[1]+'''.endr
 subq.l #4,%d0
 bgt.w .Lsecond_native
 jmp 0x40056c66
'''
 (out/'output-monitor.S').write_text(asm);cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 run('gcc','-mcpu=54418','-c',out/'output-monitor.S','-o',out/'output-monitor.o');run('ld','-Ttext',hex(CODE),'-e','om_first','-o',out/'output-monitor.elf',out/'output-monitor.o');run('objcopy','-O','binary',out/'output-monitor.elf',out/'output-monitor.bin');blob=(out/'output-monitor.bin').read_bytes();assert CODE+len(blob)<=LIMIT
 sy={v[2]:int(v[0],16) for line in run('nm',out/'output-monitor.elf').splitlines() if len(v:=line.split())==3};patches=[]
 for at,label in [(0x40056bf6,'om_first'),(0x40056c3e,'om_second')]:
  old=bytes(native[at-nb:at-nb+6]);new=b'\x4e\xf9'+struct.pack('>I',sy[label]);native[at-nb:at-nb+6]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 runtime[CODE-base:CODE-base+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),symbols=sy,patches=patches,new_state_bytes=0,hardware_tested=False)
