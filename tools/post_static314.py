"""Deux boucles du post natif : rampes nulles omises, ordre EMAC exact.

Les copies se construisent depuis les corps natifs verifies ; aucun octet
extrait de firmware n est stocke dans le depot. Staging de boot retire99000.
"""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1];CODE=0x46799000;LIMIT=0x46799800

def apply(meta,native,runtime,out,dry_bypass=False):
 base=0x46700000;nb=0x40000400;assert any(e['kind']=='remove' and e['address']<=CODE and LIMIT<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
 if dry_bypass and meta.get('post_static'):
  old=meta['post_static'];assert old['code']==CODE
  assert hashlib.sha256(runtime[CODE-base:CODE-base+old['code_bytes']]).hexdigest()==old['sha256']
  for p in old['patches']:
   at=p['at']-nb;new=bytes.fromhex(p['new']);assert native[at:at+len(new)]==new
   native[at:at+len(new)]=bytes.fromhex(p['old'])
  runtime[CODE-base:LIMIT-base]=bytes(LIMIT-CODE)
 assert not any(runtime[CODE-base:LIMIT-base]);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 drive=bytes(native[0x40057084-nb:0x400570fa-nb]);blend=bytes(native[0x400571c4-nb:0x400571f0-nb])
 assert hashlib.sha256(drive).hexdigest()=='3ffc9e7f3a89eb77873af449ed7a20647be8eb03200744c190f07da078af90c2'
 assert hashlib.sha256(blend).hexdigest()=='d5bffe49232be4b21e9e49a06f9c33c6c9c3d0760c681633975741d0f1b21fee'
 for old in [bytes.fromhex('d9ef0044dbef0048')]:assert drive.count(old)==1;drive=drive.replace(old,b'')
 old=bytes.fromhex('d9ef0054daaf005cd8af0058dcaf0060');assert blend.count(old)==1;blend=blend.replace(old,b'')
 def raw(b):return '.byte '+','.join(map(str,b))+'\n'
 asm='''.text
.globl ps_drive,ps_drive_static,ps_blend,ps_blend_static
ps_drive:
 movea.l #0x80000000,%a3
 move.l 68(%sp),%d0
 or.l 72(%sp),%d0
 beq.s ps_drive_static
 jmp 0x40057080
ps_drive_static:
 moveq #31,%d2
 moveq #8,%d6
.Ldrive:
.rept 4
'''+raw(drive)+'''.endr
 subq.l #1,%d6
 bne.w .Ldrive
 jmp 0x40057100
.balign 4
ps_blend:
 move.l 84(%sp),%d0
 or.l 88(%sp),%d0
 or.l 92(%sp),%d0
 or.l 96(%sp),%d0
 beq.s ps_blend_static
 move.l (%a0),%d1
 move.l (%a1),%d2
 moveq #32,%d0
 jmp 0x400571c4
ps_blend_static:
 move.l (%a0),%d1
 move.l (%a1),%d2
 moveq #8,%d0
.Lblend:
.rept 4
'''+raw(blend)+'''.endr
 subq.l #1,%d0
 bne.w .Lblend
 jmp 0x400571f4
'''
 if dry_bypass:
  # Les deux gains wet precedents et les deux cibles doivent etre nuls.
  # Le scratch drive n est alors jamais consomme par une MAC non nulle.
  gate='''
 moveq #0,%d6
 movea.l 60(%sp),%a3
 mvs.w (%a3),%d0
 cmpi.l #15360,%d0
 bgt.s .Ltest_second
 lea 0x40a78c2c,%a3
 tst.l (%a3,%d7.l)
 bne.s .Ltest_second
 moveq #1,%d6
.Ltest_second:
 movea.l 60(%sp),%a3
 mvs.w 66(%a3),%d0
 cmpi.l #15360,%d0
 bgt.s .Lchoose_drive
 lea 0x40a78c2c,%a3
 tst.l 4(%a3,%d7.l)
 bne.s .Lchoose_drive
 bset #1,%d6
.Lchoose_drive:
 movea.l #0x80000000,%a3
 cmpi.l #1,%d6
 beq.w ps_drive_second
 cmpi.l #2,%d6
 beq.w ps_drive_first
 cmpi.l #3,%d6
 bne.s .Ldrive_needed
.globl ps_drive_dry
ps_drive_dry:
 movclr.l %acc3,%d0
 jmp 0x40057100
.Ldrive_needed:
'''
  asm=asm.replace('ps_drive:\n','ps_drive:\n'+gate,1)
  for channel in ('second','first'):
   body=''
   if channel=='first':body+=' mac.l %a5,%d1,%acc3\n adda.l 72(%sp),%a5\n move.l %acc3,%d4\n move.l %d4,%d5\n asr.l %d2,%d5\n'
   else:body+=' adda.l 68(%sp),%a4\n move.l %acc2,%d0\n move.l %d0,%d3\n asr.l %d2,%d3\n'
   value,sign,acc=('%d4','%d5','%acc3') if channel=='first' else ('%d0','%d3','%acc2')
   for iteration in range(3):
    body+=f' move.l {value},%d1\n eor.l {sign},%d1\n msac.l %a3,{value},{acc}\n msac.l {value},%d1,{acc}\n'
    if iteration<2:body+=f' move.l {acc},{value}\n'
   if channel=='first':body+=' move.l (%a0)+,%d1\n movclr.l %acc3,%d4\n move.l %d4,(%a1)+\n'
   else:body+=' move.l 128(%a0),%d5\n movclr.l %acc2,%d0\n move.l %d0,(%a2)+\n mac.l %a4,%d5,(%a0)+,%d1,%acc2\n'
   asm+=f'\n.globl ps_drive_{channel}\nps_drive_{channel}:\n moveq #31,%d2\n moveq #8,%d6\n.Ldrive_{channel}:\n.rept 4\n'+body+f'.endr\n subq.l #1,%d6\n bne.w .Ldrive_{channel}\n jmp 0x40057100\n'
  blend_gate='''
 move.l %a4,%d0
 or.l %d4,%d0
 beq.w ps_blend_wet
 move.l %d5,%d0
 or.l %d6,%d0
 beq.w ps_blend_dry
'''
  asm=asm.replace('ps_blend_static:\n','ps_blend_static:\n'+blend_gate,1)
  for kind,body in [('wet',''' move.l (%a2)+,%d1
 mac.l %d5,%d1,%acc0
 move.l (%a3)+,%d2
 mac.l %d6,%d2,%acc1
'''),('dry',''' mac.l %a4,%d1,4(%a0),%d1,%acc0
 mac.l %d4,%d2,4(%a1),%d2,%acc1
''')]:
   asm+=f'\n.globl ps_blend_{kind}\nps_blend_{kind}:\n move.l (%a0),%d1\n move.l (%a1),%d2\n moveq #8,%d0\n.Lblend_{kind}:\n.rept 4\n'+body+f' movclr.l %acc0,%d3\n move.l %d3,(%a0)+\n movclr.l %acc1,%d3\n move.l %d3,(%a1)+\n.endr\n subq.l #1,%d0\n bne.w .Lblend_{kind}\n jmp 0x400571f4\n'
 (out/'post-static.S').write_text(asm)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 run('gcc','-mcpu=54418','-c',out/'post-static.S','-o',out/'post-static.o');run('ld','-Ttext',hex(CODE),'-e','ps_drive','-o',out/'post-static.elf',out/'post-static.o');run('objcopy','-O','binary',out/'post-static.elf',out/'post-static.bin');blob=(out/'post-static.bin').read_bytes();assert CODE+len(blob)<=LIMIT
 sy={v[2]:int(v[0],16) for line in run('nm',out/'post-static.elf').splitlines() if len(v:=line.split())==3}
 patches=[]
 for at,was,label in [(0x4005707a,bytes.fromhex('267c80000000'),'ps_drive'),(0x400571be,bytes.fromhex('221024117020'),'ps_blend')]:
  i=at-nb;assert native[i:i+6]==was;new=b'\x4e\xf9'+struct.pack('>I',sy[label]);native[i:i+6]=new;patches.append(dict(at=at,old=was.hex(),new=new.hex()))
 runtime[CODE-base:CODE-base+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),symbols=sy,patches=patches,new_state_bytes=0,quality_unchanged=True,ramps_preserved=True,samples_per_iteration=4,dry_drive_bypass=dry_bypass,single_channel_dry_bypass=dry_bypass,zero_blend_MAC_bypass=dry_bypass,hardware_tested=False)
