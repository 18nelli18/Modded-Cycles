"""Réutiliser le ladder sans remise à zéro rythmique ; contrôles et son natifs."""
import pathlib,json,struct,subprocess,hashlib
import build,sprites,ref_mainos
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/wizard-filter-continuous');stock=load_stock('firmware/model-cycles_OS1.13.syx');w=json.load(open('work/sample-wizard-main/installer.json'));ws={k:int(v,16) for k,v in w['symbols'].items()};d=json.load(open('work/genie-attack-test/data.json'));sy={k:int(v,16) for k,v in d['recipe']['symbols'].items()};cat=json.load(open('work/genie-attack-test/case-select-all.json'))['tweaks']
occ=[(x['off']+build.BASE,x['off']+build.BASE+len(x['new'])//2) for t in cat for x in t['writes']];free=[]
for a,row in sprites.MASKS.items():
 if len(row)!=4:continue
 cuts=sorted([(max(a,lo),min(a+row[0],hi)) for lo,hi in occ if a<hi and lo<a+row[0]]);cursor=a
 for lo,hi in cuts+[(a+row[0],a+row[0])]:
  start=(cursor+3)&~3
  if lo-start>=12:free.append(dict(at=start,mask=a,cap=lo-start,size=0,parts=[]))
  cursor=max(cursor,hi)
subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(P/'filter.o'),str(P/'filter.s')],check=True);parts=[]
for l in subprocess.check_output(['m68k-elf-objdump','-h',str(P/'filter.o')],text=True).splitlines():
 c=l.split()
 if len(c)>3 and c[0].isdigit() and c[1].startswith('.text.') and int(c[2],16):parts.append((c[1],int(c[2],16)))
for name,n in sorted(parts,key=lambda x:-x[1]):
 fits=[(b['cap']-b['size']-n,b) for b in free if b['size']+n<=b['cap']];assert fits,(name,n);_,b=min(fits,key=lambda x:x[0]);b['size']+=n;b['parts'].append(name)
bins=[b for b in free if b['parts']];defs=dict(FILTER_COEF=ws['gflt_coef'],FILTER_RUN=ws['gflt_run'],ATTACK_PRE=sy['ava_pre'],ATTACK_RUN=sy['ava_run'],ATTACK_OBJECTS=sy['ava_objects'])
(P/'link.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { '+''.join('.bin'+str(i)+' '+hex(b['at'])+' : { '+''.join('*('+sec+') ' for sec in b['parts'])+' } ' for i,b in enumerate(bins))+' /DISCARD/ : { *(.text) *(.data) *(.bss) } }')
subprocess.run(['m68k-elf-ld','-T',str(P/'link.ld'),'-o',str(P/'filter.elf'),str(P/'filter.o')],check=True);s={r[2]:int(r[0],16) for l in subprocess.check_output(['m68k-elf-nm',str(P/'filter.elf')],text=True).splitlines() if len(r:=l.split())==3};writes=[]
def add(at,new,old=None):writes.append(dict(off=at-build.BASE,old=(stock[at-build.BASE:at-build.BASE+len(new)] if old is None else old).hex(),new=new.hex()))
for i,b in enumerate(bins):
 subprocess.run(['m68k-elf-objcopy','-O','binary','--only-section=.bin'+str(i),str(P/'filter.elf'),str(P/'filter.bin')],check=True);raw=(P/'filter.bin').read_bytes();assert len(raw)<=b['cap'];add(b['at'],raw);writes.append(sprites.redirect_write(b['mask']));print(hex(b['at']),len(raw),b['cap'])
add(0x400a7da8,b'\x4e\xf9'+struct.pack('>I',s['avfc_pre']),b'\x4e\xf9'+struct.pack('>I',sy['ava_pre']))
add(0x401005a8,struct.pack('>I',s['avfc_objects']),struct.pack('>I',sy['ava_objects']))
for index,k,default,cc,longname,short in [(11,25,0,71,'str_greso','str_gres'),(12,24,32512,74,'str_gfilter','str_gflt')]:add(0x4010dce0+56*index,struct.pack('>14I',7,k,0,32512,default,0,(cc<<16)|65535,0xffffffff,0,0x600,72+(index==11),ws[longname],0x40129882,ws[short]))
changes=[]
def change(at,old,new):assert len(old)==len(new);changes.append(dict(at=at,old=old.hex(),new=new.hex()))
# Modifier seulement nos adaptateurs propres : même boucle Attack puis ladder continu.
code=next(x for x in d['recipe']['writes'] if x['off']+build.BASE<=sy['ava_post']<x['off']+build.BASE+len(x['new'])//2);needle=b'\x4e\xb9'+struct.pack('>I',sy['ava_run']);i=bytes.fromhex(code['new']).index(needle);change(code['off']+build.BASE+i,needle,b'\x4e\xb9'+struct.pack('>I',s['avfc_run']))
# Copier les trois descripteurs 11..13 à l'init des moteurs, pas seulement Attack.
code=next(x for x in d['recipe']['writes'] if x['off']+build.BASE<=sy['ava_boot']<x['off']+build.BASE+len(x['new'])//2);raw=bytes.fromhex(code['new'])
for old,new in [('41e802d8','41e80268'),('43f94010dfb8','43f94010df48'),('700d','7029')]:
 i=raw.index(bytes.fromhex(old));change(code['off']+build.BASE+i,bytes.fromhex(old),bytes.fromhex(new))
payload=[json.load(open(P/'reset-fix.json'))]
for x in d['payload']:
 if x['old'] in ['720c21410018','720b2141001c']:payload.append(dict(off=x['off'],old=x['new'],new=x['old']))
 for name,full in [('snd_save_post','sm_snd_save_post_full'),('snd_load_post','sm_snd_load_post_full')]:
  if x['off']==ws[name]-int(w['append']['dest'],16):payload.append(dict(off=x['off'],old=x['new'],new=(b'\x4e\xf9'+struct.pack('>I',ws[full])+b'\x4e\x71').hex()))
t=dict(id='wizard-continuous-filter',order=63,name='Filtre continu Wizard',requires=['supermodel-genie-attack'],conflicts=[],status='experimental',writes=writes,symbols={k:hex(v) for k,v in s.items() if k.startswith('avfc_')})
(P/'data.json').write_text(json.dumps(dict(recipe=t,changes=changes,payload=payload)));print('PASS continuous filter chained with Attack; per-note reset skipped, own sound codecs used, no additional startup payload')
