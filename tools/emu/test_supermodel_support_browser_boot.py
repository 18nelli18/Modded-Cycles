#!/usr/bin/env python3
"""Profils UI autonomes : image Python/navigateur, boot réel et cache disque."""
import json,pathlib,struct,hashlib
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build,syntakt
stock=main_os_from_syx('firmware/model-cycles_OS1.13.syx');st=syntakt.dsp_image('firmware/Syntakt_OS1.42.syx')
rows=json.load(open('work/supermodel-support/frontend-cases.json'))
for row in rows:
 if row['name']=='tg-optional':continue
 cat=json.load(open('work/supermodel-support/frontend-'+row['name']+'.json'))['tweaks'];image,_=build.apply_writes(stock,cat);full=bytes(image)
 for t in sorted(cat,key=lambda t:t['order']):
  ap=t.get('append')
  if not ap:continue
  at=int(ap['at'],16)
  if at>build.BASE+len(full):assert t['id']=='supermodel-support-independent' and at==0x401f8f76;full+=bytes(at-build.BASE-len(full))
  assert at==build.BASE+len(full);full+=build.payload_image(t,build.payload_runtime(t,stock,st))
 assert hashlib.sha256(full).hexdigest()==row['sha'],row['name']
 t=next(x for x in cat if x['id']=='supermodel-support-independent');r=Rig(full,{'writes':[]},{'writes':[],'symbols':t['symbols']});u=r.u
 u.mem_map(0x43000000,0x1000000);u.mem_map(0x46700000,0x400000);u.mem_map(0x80000000,0x200000)
 u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
 def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
 ranges=[(build.BASE,full)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for x in cat for p in x.get('append',{}).get('parts',[]) if 'hex' in p]
 sites={at+i for at,b in ranges for i in range(0,len(b)-3,2) if b[i:i+2]==b'\x4e\x7b'}
 for pc in sites:u.hook_add(UC_HOOK_CODE,cache,begin=pc,end=pc)
 u.emu_start(0x40000530,0x4000053a,count=35000000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a,row['name']
 raw=build.payload_runtime(t,stock,None);origin=int(t['append']['dest'],16);assert bytes(u.mem_read(origin,len(raw)))==raw
 r.call(0x4007929c);nodes=[];p=r.r32(0x401eb894)
 while p:assert p not in nodes;nodes.append(p);p=r.r32(p+12)
 assert len(nodes)==16-t['cache_blocks'];assert bytes(u.mem_read(origin,len(raw)))==raw
 print('PASS native boot/cache + browser/Python',row['name'],flush=True)
print('NOTE: physical cache and MIDI/display peripherals not simulated')
