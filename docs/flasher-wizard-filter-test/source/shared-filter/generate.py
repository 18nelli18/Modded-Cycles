"""Partage du filtre Wizard sans chevaucher k28..32 ni le record LFO2+88."""
import json,pathlib,subprocess,struct,hashlib
import build,sprites,ref_mainos
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/wizard-filter-integration');w=json.load(open('work/sample-wizard-main/installer.json'));s={k:int(v,16) for k,v in w['symbols'].items()};stock=load_stock('firmware/model-cycles_OS1.13.syx')
slots=[(0x4015c9ba,86,'.text.avf_pre',0x4015c9a4),(0x40195a7c,124,'.text.avf_post',0x40195a7c),(0x4015bf40,80,'.text.avf_ui',0x4015bf24),(0x4017985c,76,'.text.avf_maps',0x40179730)]
defs=dict(VOICE_PTR=s['voice_ptr'],FILTER_COEF=s['gflt_coef'],FILTER_RUN=s['gflt_run'],SAMPLER_PRE=s['sampler_pre'])
(P/'link.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { '+''.join(sec+' '+hex(a)+' : { '+('*(.text.avf_pre) *(.text.avf_conv)' if sec=='.text.avf_pre' else '*(.text.avf_objects) *(.text.avf_boot)' if sec=='.text.avf_ui' else '*('+sec+')')+' } ASSERT(SIZEOF('+sec+') <= '+str(cap)+', "cave pleine") ' for a,cap,sec,mask in slots)+' }')
subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(P/'shared.o'),str(P/'shared.s')],check=True);subprocess.run(['m68k-elf-ld','-T',str(P/'link.ld'),'-o',str(P/'shared.elf'),str(P/'shared.o')],check=True)
sy={r[2]:int(r[0],16) for l in subprocess.check_output(['m68k-elf-nm',str(P/'shared.elf')],text=True).splitlines() if len(r:=l.split())==3};writes=[]
def add(a,new,old=None):
 if old is None:old=stock[a-build.BASE:a-build.BASE+len(new)]
 assert len(old)==len(new);writes.append(dict(off=a-build.BASE,old=old.hex(),new=new.hex()))
for va,cap,sec,mask in slots:
 subprocess.run(['m68k-elf-objcopy','-O','binary','--only-section='+sec,str(P/'shared.elf'),str(P/'shared.bin')],check=True);code=(P/'shared.bin').read_bytes();assert len(code)<=cap
 for path in pathlib.Path('work/sample-wizard-options').glob('case-*.json'):
  for t in json.load(open(path))['tweaks']:
   if t['id']=='track-filter':continue
   for x in t['writes']:assert not(va<x['off']+build.BASE+len(x['new'])//2 and x['off']+build.BASE<va+len(code)),(path,t['id'],hex(va))
 add(va,code);writes.append(sprites.redirect_write(mask));print(sec,len(code),'/',cap)
add(0x400a7da8,b'\x4e\xf9'+struct.pack('>I',sy['avf_pre']),b'\x4e\xf9'+struct.pack('>I',s['sampler_pre']))
add(0x40059852,b'\x4e\xb9'+struct.pack('>I',sy['avf_post']))
add(0x401005a8,struct.pack('>I',sy['avf_objects']))
add(0x4004486c,b'\x4e\xb9'+struct.pack('>I',sy['avf_boot']))
for index,k,default,cc,longname,short in [(11,25,0,71,'str_greso','str_gres'),(12,24,32512,74,'str_gfilter','str_gflt')]:
 add(0x4010dce0+56*index,struct.pack('>14I',7,k,0,32512,default,0,(cc<<16)|65535,0xffffffff,0,0x600,72+(index==11),s[longname],0x40129882,s[short]))
add(0x4005b9c6,b'\x4e\xb9'+struct.pack('>I',sy['avf_lock_save'])+b'\x4e\x71')
add(0x4005bad2,b'\x4e\xb9'+struct.pack('>I',sy['avf_lock_update']))
add(0x4005aa34,b'\x4e\xf9'+struct.pack('>I',sy['avf_lock_conv']))
add(0x4005b816,bytes.fromhex('7a21'))
# Post-codec commun existant, mêmes emplacements que Wizard, sans toucher LFO2.
changes=[];raw=bytes.fromhex(w['append']['parts'][0]['hex']);dest=int(w['append']['dest'],16)
for name in ['snd_save_post','snd_load_post']:
 at=s[name];i=at-dest;b=raw[i:i+24];needle=bytes.fromhex('0c810000000667000006508f4e75');off=b.index(needle)+6;assert raw[i+off:i+off+4]==bytes.fromhex('67000006');changes.append(dict(off=i+off,old='67000006',new='60000006'))
t=dict(id='wizard-shared-filter',order=49,name='Filtre Wizard partagé',description=['Filtre ladder quatre pôles : MACHINES + SWEEP = coupure, MACHINES + CONTOUR = résonance.','Pistes synth/drum : k24/25 ; Wizard garde son filtre. LFO2 k28..32 et record+88 préservés.'],requires=['sample-wizard'],conflicts=[],status='experimental',writes=writes,symbols={k:hex(v) for k,v in sy.items() if k.startswith('avf_')})
(P/'recipe.json').write_text(json.dumps(dict(recipe=t,changes=changes,ref=dict(w=hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest()))));print('PASS shared hooks, descriptors, free-tail guards; two conditional codec branches only')
