"""Démarrage réel de sélections distinctes, dont aucune machine Syntakt.

MOVEC cache non simulé ; code, cache LRU et tables CHORD sont contrôlés.
Les tests n'envoient rien au matériel et n'exportent aucune image OS.
"""
import json,pathlib,struct,hashlib,copy
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig,STACK,STOP
from chord_keys_pr87 import load_stock
import build,syntakt,gen_syntakt_engines as gs
P=pathlib.Path('work/preview-chord-test');stock=load_stock('firmware/model-cycles_OS1.13.syx');st=syntakt.dsp_image('firmware/Syntakt_OS1.42.syx');packs=json.load(open('work/sample-wizard-options/private-packed.json'))
for name in ['full-with-wave','no-extra-machines']:
 row=json.load(open(P/('case-'+name+'.json')));cat=copy.deepcopy(row['tweaks']);w=next(t for t in cat if t['id']=='sample-wizard');ck=next((t for t in cat if t['id']=='chord-keys-supermodel'),None)
 for t in cat:
  if t['id'].startswith('wizard-machines-'):t['append']['compressed_hex']=packs[t['id'].split('-')[-1]]
 image,_=build.apply_writes(stock,cat);payload,_=build.build_payload(cat,stock,'firmware/Syntakt_OS1.42.syx');full=bytes(image)+payload;assert hashlib.sha256(full).hexdigest()==row['sha'],name
 r=Rig(full,{'writes':[]},{'writes':[],'symbols':w['symbols']});u=r.u;u.mem_map(0x46700000,0x100000);u.mem_map(0x80000000,0x200000)
 for lo,hi,to in gs.CY_SRAM_INIT:u.mem_write(to,full[lo-build.BASE:hi-build.BASE])
 original=[(struct.unpack_from('>I',stock,gs.CHORD_PTRS-build.BASE+4*i)[0],None) for i in range(31)];expected=[bytes(u.mem_read(at,64)) for at,_ in original]
 ranges=[(build.BASE,full)]+[(int(t['append']['dest'],16),build.payload_runtime(t,stock,st)) for t in cat if t.get('append')]
 def skip(uc,pc,size,user):uc.reg_write(m.UC_M68K_REG_PC,pc+4)
 for pc in {at+i for at,b in ranges for i in range(0,len(b)-3,2) if b[i:i+2]==b'\x4e\x7b'}:u.hook_add(UC_HOOK_CODE,skip,begin=pc,end=pc)
 u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(m.UC_M68K_REG_A7,STACK);u.emu_start(0x40000530,0x4000053a,count=45000000);assert u.reg_read(m.UC_M68K_REG_PC)==0x4000053a,name
 raw=build.payload_runtime(w,stock,st);assert bytes(u.mem_read(int(w['append']['dest'],16),len(raw)))==raw,(name,'Wizard')
 if ck:
  rawck=build.payload_runtime(ck,stock,st);assert bytes(u.mem_read(int(ck['append']['dest'],16),len(rawck)))==rawck,(name,'ChordKeys')
 for i,want in enumerate(expected):assert bytes(u.mem_read(r.r32(gs.CHORD_PTRS+4*i),64))==want,(name,'CHORD table',i)
 r.call(0x4007929c);nodes=[];p=r.r32(0x401eb894);prev=0
 while p:
  assert p not in nodes and r.r32(p+16)==prev;nodes.append(p);prev=p;p=r.r32(p+12)
 assert nodes==[0x401eb750+20*i for i in range(w['cache_blocks'],16)],name
 assert bytes(u.mem_read(int(w['append']['dest'],16),len(raw)))==raw,name
 f=next(t for t in cat if t['id']=='supermodel-genie-attack');sy={k:int(v,16) for k,v in f['symbols'].items()};r.call(sy['ava_boot']);desc=r.r32(0x4005a2de);assert bytes(u.mem_read(desc+728,56))==bytes(u.mem_read(0x4010dfb8,56)),name
 print('PASS native startup/cache/code and 31 CHORD tables',name,flush=True)
print('PASS deux sélections natives ; cache physique non simulé ; validation matérielle attendue.')
