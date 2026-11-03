"""Biquad natif DFI : coefficients et historiques en registres, ordre EMAC exact.

Les plages buffer128octets et etat20octets doivent etre disjointes. Sinon
rejouer la routine native complete, y compris son ordre de lectures/ecritures.
Pas de restrict, de changement d'arrondi ou de changement du gouverneur.
"""
from pathlib import Path
import hashlib,os,struct,subprocess
BASE=0x40000400;ENTRY=0x400a9cf6;END=0x400a9d4e;CODE=0x46799a00;LIMIT=0x4679a200

def apply(meta,native,runtime,stock,out):
 assert not meta.get('native_biquad')
 old=bytes(stock[ENTRY-BASE:END-BASE]);assert native[ENTRY-BASE:END-BASE]==old and old[:6].hex()=='4feffff04280'
 assert not any(runtime[CODE-0x46700000:LIMIT-0x46700000])
 assert any(x['kind']=='remove' and x['address']<=CODE and LIMIT<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
 source='''.text
.globl entry
entry:
 movea.l 4(%sp),%a1
 movea.l 8(%sp),%a0
 move.l %a1,%d0
 sub.l %a0,%d0
 cmpi.l #20,%d0
 bcs.w fallback
 move.l %a0,%d0
 sub.l %a1,%d0
 cmpi.l #128,%d0
 bcs.w fallback
 lea -32(%sp),%sp
 movem.l %d2-%d7/%a2-%a3,(%sp)
 move.l (%a0),%d6
 move.l 4(%a0),%d7
 movea.l 8(%a0),%a2
 move.l 12(%a0),%d4
 move.l 16(%a0),%d5
 lea 128(%a1),%a3
loop:
.rept 2
 move.l (%a1),%d2
 mac.l %d7,%d4,%acc0
 movclr.l %acc0,%d3
 mac.l %d6,%d2,%acc0
 movclr.l %acc0,%d1
 add.l %d3,%d1
 msac.l %a2,%d5,%acc0
 movclr.l %acc0,%d3
 add.l %d3,%d1
 move.l %d2,%d4
 move.l %d1,(%a1)+
 move.l %d1,%d5
.endr
 cmpa.l %a3,%a1
 bne.w loop
 move.l %d4,12(%a0)
 move.l %d5,16(%a0)
 moveq #32,%d0
 moveq #32,%d1
 cmp.l %d0,%d1
 movem.l (%sp),%d2-%d7/%a2-%a3
 lea 32(%sp),%sp
 rts
fallback:
'''+'.byte '+','.join(map(str,old))+'\n'
 out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'native-biquad.S').write_text(source)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 run('gcc','-mcpu=54418','-c',out/'native-biquad.S','-o',out/'native-biquad.o');run('ld','-Ttext',hex(CODE),'-e','entry','-o',out/'native-biquad.elf',out/'native-biquad.o');run('objcopy','-O','binary',out/'native-biquad.elf',out/'native-biquad.bin')
 blob=(out/'native-biquad.bin').read_bytes();assert CODE+len(blob)<=LIMIT
 sy={v[2]:int(v[0],16) for line in run('nm',out/'native-biquad.elf').splitlines() if len(v:=line.split())==3}
 patch=dict(at=ENTRY,old=old[:6].hex(),new=(b'\x4e\xf9'+struct.pack('>I',CODE)).hex())
 native[ENTRY-BASE:ENTRY-BASE+6]=bytes.fromhex(patch['new']);runtime[CODE-0x46700000:CODE-0x46700000+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),symbols=sy,patches=[patch],new_state_bytes=0,overlap_fallback=True,hardware_tested=False)
