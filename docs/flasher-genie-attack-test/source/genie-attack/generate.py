"""Lampe Genie, pads mute et Attack sans filtre partagé."""
import pathlib,json,subprocess,struct,hashlib,re
import build,sprites,ref_mainos
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/genie-attack-test');stock=load_stock('firmware/model-cycles_OS1.13.syx');w=json.load(open('work/sample-wizard-main/installer.json'));ws={k:int(v,16) for k,v in w['symbols'].items()};sg=json.load(open('work/genie-queue-choice/recipes.json'))['wizard'];ss={k:int(v,16) for k,v in sg['symbols'].items()}
paths=list(pathlib.Path('work/sample-wizard-options').glob('case-*.json'))+list(pathlib.Path('work/genie-queue-choice').glob('case-*.json'))
occ=[(0x4015c9a4,0x4015ca20),(0x40179730,0x401798a8)]+[(x['off']+build.BASE,x['off']+build.BASE+len(x['new'])//2) for p in paths for cat in [json.load(open(p))['tweaks']] if any(t['id']=='sample-wizard' for t in cat) for t in cat if t['id'] not in ['track-filter','lfo-plus'] for x in t['writes']]
objects=[]
for name in ['ui','attack']:
 o=P/(name+'.o');subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(o),str(P/(name+'.s'))],check=True);objects.append(o)
parts=[]
for o in objects:
 for l in subprocess.check_output(['m68k-elf-objdump','-h',str(o)],text=True).splitlines():
  c=l.split()
  if len(c)>3 and c[0].isdigit() and c[1].startswith(('.text.','.data.')) and int(c[2],16):parts.append((c[1],int(c[2],16),1<<int(c[6][3:]) if len(c)>6 else 4))
free=[]
for a,r in sprites.MASKS.items():
 if len(r)!=4:continue
 cuts=sorted([(max(a,lo),min(a+r[0],hi)) for lo,hi in occ if a<hi and lo<a+r[0]])
 cursor=a
 for lo,hi in cuts+[(a+r[0],a+r[0])]:
  start=(cursor+3)&~3
  if lo-start>=12:free.append(dict(at=start,mask=a,cap=lo-start,size=0,parts=[]))
  cursor=max(cursor,hi)

for name,n,align in sorted(parts,key=lambda x:-x[1]):
 align=max(align,4);fits=[]
 for b in free:
  at=(b['size']+align-1)&-align
  if at+n<=b['cap']:fits.append((b['cap']-at-n,b['at'],at,b))
 assert fits,(name,n,sorted([(hex(b['at']),b['cap']-b['size']) for b in free],key=lambda x:-x[1])[:8])
 _,_,off,b=min(fits,key=lambda x:(x[0],x[1]));b['size']=off+n;b['parts'].append(name)
bins=[b for b in free if b['parts']];defs={**{k:ws[v] for k,v in dict(ATK_KEY='atk_key',ATK_GAIN='atk_gain',ATK_STEP='atk_step',SAMPLER_PRE='sampler_pre',TRK_MACH='trk_mach',SAVE_FULL='sm_snd_save_post_full',LOAD_FULL='sm_snd_load_post_full').items()},**{k:ss[v] for k,v in dict(SG_VT='sg_vt',SG_PAD='sg_pad',SG_FUNC='sg_func',SG_FMT='sg_fmt_s',SG_DTOR0='sg_dtor0',SG_DTOR1='sg_dtor1').items()}}
script='\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { '+''.join('.bin'+str(i)+' '+hex(b['at'])+' : { '+''.join('. = ALIGN(4); *('+n+') ' for n in b['parts'])+' }' for i,b in enumerate(bins))+' /DISCARD/ : { *(.text) *(.data) *(.bss) } }'
(P/'link.ld').write_text(script);subprocess.run(['m68k-elf-ld','--no-warn-rwx-segments','--orphan-handling=error','-T',str(P/'link.ld'),'-o',str(P/'test.elf'),*map(str,objects)],check=True)
s={r[2]:int(r[0],16) for l in subprocess.check_output(['m68k-elf-nm',str(P/'test.elf')],text=True).splitlines() if len(r:=l.split())==3};writes=[]
def add(va,new,old=None):
 old=stock[va-build.BASE:va-build.BASE+len(new)] if old is None else old;assert len(new)==len(old);writes.append(dict(off=va-build.BASE,old=old.hex(),new=new.hex()))
for i,b in enumerate(bins):
 subprocess.run(['m68k-elf-objcopy','-O','binary','--only-section=.bin'+str(i),str(P/'test.elf'),str(P/'test.bin')],check=True);raw=(P/'test.bin').read_bytes();assert len(raw)<=b['cap'];add(b['at'],raw);writes.append(sprites.redirect_write(b['mask']));print(hex(b['at']),len(raw),b['cap'],b['parts'])
# Une seule recette auxiliaire ; UI active seulement avec Genie, Attack avec Wizard.
t=dict(id='supermodel-genie-attack',name='Lampe Genie et Attack partagée',order=62,status='experimental',requires=[],conflicts=['lfo-plus'],writes=writes,symbols={k:hex(v) for k,v in s.items() if k.startswith(('avg_','ava_'))})
# Changements propres à Genie, après la queue Page/Loop déjà vérifiée.
changes=[]
def ch(at,old,new):assert len(old)==len(new);changes.append(dict(at=at,old=old.hex(),new=new.hex()))
def get(at,n):
 x=next(x for x in sg['writes'] if x['off']+build.BASE<=at and at+n<=x['off']+build.BASE+len(x['new'])//2);i=at-x['off']-build.BASE;return bytes.fromhex(x['new'])[i:i+n]
# Libellés courts et x à droite du cartouche, sans toucher les valeurs/queue.
for name,label in [('sg_sl0','Scl')]:pass
body=get(ss['sg_render'],170);idx=body.index(bytes.fromhex('48780002487940ea14cc'));ch(ss['sg_render']+idx,bytes.fromhex('48780002'),bytes.fromhex('4878002c'))
# Épilogue partagé : panneau puis restauration ABI originale.
needle=bytes.fromhex('4cd7043c4fef00144e75');hits=[(x,bytes.fromhex(x['new']).index(needle)) for x in sg['writes'] if needle in bytes.fromhex(x['new'])];assert len(hits)==1;wx,idx=hits[0];tail=wx['off']+build.BASE+idx;body=bytes.fromhex(wx['new']);va=wx['off']+build.BASE;ch(tail,needle[:8],b'\x4e\xf9'+struct.pack('>I',s['avg_render_end'])+b'\x4e\x71')
# Les origines du surlignage passent à x42/x84.
start=body.index(bytes.fromhex('70004ab9'));ch(va+start,bytes.fromhex('7000'),bytes.fromhex('702a'));i=body.index(bytes.fromhex('7040'));ch(va+i,bytes.fromhex('7040'),bytes.fromhex('7054'))
# Construire le LedHandler privé ; remplacer le chargement existant du callback pad.
va=ss['sg_o_allocate'] if 'sg_o_allocate' in ss else ss['sg_open']
# Trouver dans les écritures le move.l #sg_pad,d0 unique.
needle=b'\x20\x3c'+struct.pack('>I',ss['sg_pad']);hits=[]
for x in sg['writes']:
 b=bytes.fromhex(x['new']);hits += [build.BASE+x['off']+i for i in range(0,len(b)-5,2) if b[i:i+6]==needle]
assert len(hits)==1,hits;ch(hits[0],needle,b'\x4e\xb9'+struct.pack('>I',s['avg_open_led']))
# Réutiliser les noms courts de l'UI lamp originale dans une table propre.
labels=re.search(r'sg_stock_labels:\n(.*)',pathlib.Path('tools/machines/seq_gen/stock_ui.s').read_text(),re.S).group(1)
# Les noms actuels sont remplacés par leurs préfixes courts avec bourrage NUL (pas de déplacement).
shorts=['Scl','Key','Lo','Hi','Den %','Vel','V.Min','V.Max','Dec','D.Min','D.Max','Pan','P.Min','P.Max','Target','Mut %','Rhythm','Hits','Rot','Queue','Generate','Undo','Sound','Undo']
for i,label in enumerate(shorts):
 ptr=int.from_bytes(get(ss['sg_labels']+4*i,4),'big');text=get(ptr,1);n=0
 while get(ptr+n,1)!=b'\0':n+=1
 b=label.encode()+b'\0'
 if len(b)<=n+1:ch(ptr,get(ptr,n+1),b+bytes(n+1-len(b)))
# Hooks Attack, descripteur commun et table active des moteurs optionnels.
attack=[]
def ah(at,new,old=None):attack.append(dict(off=at-build.BASE,old=(stock[at-build.BASE:at-build.BASE+len(new)] if old is None else old).hex(),new=new.hex()))
ah(0x400a7da8,b'\x4e\xf9'+struct.pack('>I',s['ava_pre']),b'\x4e\xf9'+struct.pack('>I',ws['sampler_pre']))
ah(0x401005a8,struct.pack('>I',s['ava_objects']))
ah(0x40059852,b'\x4e\xb9'+struct.pack('>I',s['ava_post']))
ah(0x4004486c,b'\x4e\xb9'+struct.pack('>I',s['ava_boot']))
# Descripteur id13 : Attack commune, CC3 inutilisé par le MIDI natif de cette variante.
ah(0x4010dfb8,struct.pack('>14I',7,23,0,32512,0,0,0xffffffff,0xffffffff,0,0,35,ws['str_attack'],0x40129882,ws['str_atk']))
raw=bytes.fromhex(w['append']['parts'][0]['hex']);base=int(w['append']['dest'],16);payload=[]
for name,target in [('snd_save_post','ava_save'),('snd_load_post','ava_load')]:
 off=ws[name]-base;payload.append(dict(off=off,old=raw[off:off+8].hex(),new=(b'\x4e\xf9'+struct.pack('>I',s[target])+b'\x4e\x71').hex()))
# Ne pas exposer les deux contrôles Filter/Res supprimés quand modifier est tenu sur un synth.
lo=ws['dh_pass']-base;hi=ws['dh_stock']-base
for h in ['720c21410018','720b2141001c']:
 n=raw.find(bytes.fromhex(h),lo,hi);assert n>=0,h;payload.append(dict(off=n,old=h,new='4e71'*3))
# Le mapper de pools étendus est séparé du DSP du filtre ; garde Harmony k32/id33.
f=json.load(open('work/wizard-filter-integration/recipe.json'))['recipe'];pool=[x for x in f['writes'] if x['off']+build.BASE in [0x4005b9c6,0x4005bad2,0x4005aa34,0x4005b816,0x4017985c]]
for mask in [0x4015c9a4,0x40179730]:pool.append(sprites.redirect_write(mask))
conv=int(f['symbols']['avf_lock_conv'],16);x=next(x for x in f['writes'] if x['off']+build.BASE<=conv<x['off']+build.BASE+len(x['new'])//2);i=conv-x['off']-build.BASE;pool.append(dict(off=conv-build.BASE,old=x['old'][i*2:],new=x['new'][i*2:]))
# Réserver ces helpers codec avant allocation : les masques sont volontairement fixes de l'ancien filtre.
for x in pool:
 for y in t['writes']:assert not(x['off']<y['off']+len(y['new'])//2 and y['off']<x['off']+len(x['new'])//2),(hex(x['off']),hex(y['off']))
(P/'data.json').write_text(json.dumps(dict(recipe=t,sg=changes,attack=attack,payload=payload,pool=pool)));print('PASS UI et Attack propres générés ; aucun DSP filtre, aucune sauvegarde MIDI')
