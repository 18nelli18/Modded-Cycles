#!/usr/bin/env python3
"""Tables machines pour chaque choix TINY/RETROSYN, sans recompiler les voix.

Les corps natifs restent identiques ; seuls les menus, descripteurs et crochets
communs sont regeneres. Les donnees officielles ne quittent jamais firmware/.
"""
import argparse,copy,hashlib,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'emu')]
import gen_retrosyn as R,gen_syntakt_engines as gs,gen_sdvintage_7th as g7
import build,syntakt
ROOT=HERE.parent
CODES=['sd','cp','toy','bits','swarm']

def intersect(a,b):
 return a['off']<b['off']+len(b['new'])//2 and b['off']<a['off']+len(a['new'])//2

def generate(stock,st,tiny,wiz,mask,wizard):
 full=copy.deepcopy(tiny['variants']['511'] if wizard else tiny['normal']['255'])
 base=full['engine'];pay=int(base['append']['dest'],16);gs.set_base(pay)
 parts=base['append']['parts'];first=7 if wizard else 6;nm=first+9
 def read(at,n):
  for p in parts:
   if 'hex' in p:
    lo=int(p['dest'],16);raw=bytes.fromhex(p['hex'])
    if lo<=at and at+n<=lo+len(raw):return raw[at-lo:at-lo+n]
  raise ValueError(hex(at))
 def u32(at):return int.from_bytes(read(at,4),'big')
 def string(at):
  raw=bytearray()
  while (c:=read(at+len(raw),1))!=b'\0':raw.extend(c)
  return raw.decode('ascii')
 data=pay+0x33800;desc=pay+0x33d00
 machines=[]
 for j,bit in zip(range(5,9),(32,64,128,256)):
  if not mask&bit:continue
  index=first+j;d=desc+(g7.NDESC+5*j)*g7.DSTRIDE
  knobs=[]
  for k in range(4):
   at=d+k*g7.DSTRIDE
   knobs.append((string(u32(at+44)),string(u32(at+52)),u32(at+16)>>8,u32(at+8)>>8,u32(at+12)>>8))
  name=string(u32(data+4*index))
  machines.append(dict(name=name,label=name,image=4,decay=u32(d+4*g7.DSTRIDE+16)>>8,knobs=knobs,
                       update=u32(data+4*(nm+index)),render=u32(data+4*(2*nm+index))))
 retro=json.loads((R.DEV/('29-retrosyn-all-machines-wizard.json' if wizard else '28-retrosyn-all-machines.json')).read_text(encoding='utf-8'))
 if mask&512:machines.append(dict(R.MACHINE,label='RETROSYN',update=int(retro['symbols']['retrosyn_update'],16),render=int(retro['symbols']['retrosyn_render'],16)))
 gs.set_base(pay);an=gs.analyse(st,gs.generation(CODES));lay=an['lay']
 syms={k:int(v,16) for k,v in base['gov'].items()}
 for j,c in enumerate(CODES):
  engine=gs.CATALOG[c]['engine'];index=first+j
  syms[f"bridge_update_{engine}"]=u32(data+4*(nm+index));syms[f"bridge_render_{engine}"]=u32(data+4*(2*nm+index))
 hot=[(at,bytes.fromhex(p['hex']),run) for at,run,n in lay['tails'] for p in parts if int(p['dest'],16)==at and 'hex' in p]
 br=dict(bridge=read(pay+0x31000,324),hot=hot,syms=syms,gov=base['gov'])
 sampler=None;context=None
 if wizard:
  sampler=copy.deepcopy(wiz['variants']['0']['wizard'])
  sampler['writes']=[w for w in sampler['writes'] if w['off']!=gs.gx.CAVE-gs.BASE]
  root=next(w for w in sampler['writes'] if w['off']==gs.BOOT_CALL-gs.BASE)
  root['new']='4eb9'+sampler['symbols']['boot_extra_hook'][2:].zfill(8)
  current,_=build.apply_writes(stock,[sampler]);current=bytearray(current)
  red=gs.sprites.redirect_write(gs.gx.CAVE);current[red['off']:red['off']+len(bytes.fromhex(red['old']))]=bytes.fromhex(red['old'])
  ap=sampler['append'];context={k:int(v,16) for k,v in sampler['symbols'].items()}
  context.update(img=bytes(current),blob=bytes.fromhex(ap['parts'][0]['hex']),blob_at=int(ap['dest'],16),at=int(ap['at'],16)+ap['size'],id='sample-wizard',symbols_hex=sampler['symbols'])
  stub=next(bytes.fromhex(p['hex']) for p in parts if int(p['dest'],16)==pay+0x32a00)
  needle=bytes.fromhex('2f032f024eb9');at=stub.index(needle)+len(needle);syms['voice_done']=int.from_bytes(stub[at:at+4],'big')
 # WAVE conserve son propre indice ; TINY et RETROSYN sont places apres elle.
 prefix=mask&255
 source=wiz['variants'][str(prefix)] if wizard else (tiny['normal']['128'] if mask&128 else None)
 if mask&128:
  wp=source['engine']['append']['parts']
  native_wave=[copy.deepcopy(p) for p in wp if 'hex' in p and pay+0x79000<=int(p['dest'],16)<pay+0x7c000]
  if not wizard:
   ui=next(p for p in native_wave if int(p['dest'],16)==pay+0x7a580);raw=bytearray.fromhex(ui['hex']);assert raw[0x35]==6;raw[0x35]=6+(mask&31).bit_count()+bool(mask&32)+bool(mask&64);ui['hex']=raw.hex()
 else:native_wave=[]
 ranges=[(32,0x42000,0x76000),(64,0x76000,0x79000),(256,0x7c000,0x84000)]
 reused=[copy.deepcopy(p) for p in parts if any(mask&bit and pay+lo<=int(p['dest'],16)<pay+hi for bit,lo,hi in ranges)]+native_wave
 if mask&512:reused.extend(copy.deepcopy(p) for p in retro['append']['parts'] if int(p['dest'],16)==pay+0x85000)
 original=dict(gs.LAYOUT);maxextra=gs.MAX_EXTRA;row=gs.MARKS_ROW;marks=dict(gs.MARKS);generation=gs.generation
 try:
  gs.LAYOUT.update(STUBS=0x88000,DATA=0x89000,DESCN=0x89400,ROWSN=0x84000,CCROWSN=0x84400,RECS=0x84800)
  gs.MAX_EXTRA=10;gs.MARKS_ROW=9;gs.MARKS['x']=68;gs.set_base(pay)
  gs.generation=lambda _:generation(CODES)
  own=dict(machines=machines,bridge=br,end=pay+0x8b000,boot2=((lay['end']+15)&~15,pay+0x42000),parts=reused)
  codes=[c for i,c in enumerate(CODES) if mask&(1<<i)]
  out,_=gs.build_tweak(stock,st,codes,tg=context,own=own)
 finally:
  gs.generation=generation;gs.LAYOUT.clear();gs.LAYOUT.update(original);gs.MAX_EXTRA=maxextra;gs.MARKS_ROW=row;gs.MARKS.clear();gs.MARKS.update(marks);gs.set_base(pay)
 if not mask&31:
  ap=out['append'];ap['parts']=[p for p in ap['parts'] if 'syntakt' not in p];del ap['syntakt']
  reloc={p[0] for p in an['patches']}
  ap['reloc']=[p for p in ap['reloc'] if int(p[0],16) not in reloc]
 extras=(source['wizard']['writes'] if wizard else source['engine']['writes']) if source else []
 if wizard:
  sampler['append']=copy.deepcopy(source['wizard']['append'])
  for w in extras:
   if any(intersect(w,n) for n in out['writes']):continue
   hits=[n for n in sampler['writes'] if intersect(w,n)]
   if hits:
    lo=min([w['off']]+[n['off'] for n in hits]);hi=max([w['off']+len(w['new'])//2]+[n['off']+len(n['new'])//2 for n in hits])
    raw=bytearray(stock[lo:hi])
    for n in hits+[w]:raw[n['off']-lo:n['off']-lo+len(n['new'])//2]=bytes.fromhex(n['new'])
    sampler['writes']=[n for n in sampler['writes'] if n not in hits]+[dict(off=lo,old=stock[lo:hi].hex(),new=raw.hex())]
   else:sampler['writes'].append(copy.deepcopy(w))
 else:
  for w in extras if mask&128 else []:
   if any(intersect(w,n) for n in out['writes']):continue
   row=copy.deepcopy(w);row['old']=stock[row['off']:row['off']+len(row['new'])//2].hex();out['writes'].append(row)
 out.update(id='machine-selection-'+str(mask)+('-wizard' if wizard else ''),order=29,status='experimental',requires=['sample-wizard'] if wizard else [],conflicts=[],
            machine_names=['Kick','Snare','Metal','Perc','Tone','Chord']+(['Sampler'] if wizard else [])+[gs.CATALOG[c]['name'] for c in codes]+[m['name'] for m in machines])
 out['append'].update(compress_cost=512,compress_margin=0)
 out['name']='Selection de machines independantes'
 out['description']=['Machines ajoutees choisies independamment ; Sample Wizard facultatif.', 'Corps natifs conserves ; interfaces regenerees. tools/gen_machine_combinations.py ; notes/118.']
 out['machine_selection']=mask
 out['machine_tables']=hex(pay+0x89000)
 out['writes'].sort(key=lambda w:w['off'])
 build.apply_writes(stock,([sampler] if wizard else [])+[out])
 return dict(engine=out,engine_sha256=hashlib.sha256(json.dumps(out,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),**({'wizard':sampler} if wizard else ({'wave':dict(copy.deepcopy(source['wave']),index=6+(mask&31).bit_count()+bool(mask&32)+bool(mask&64))} if mask&128 else {})))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--masks',default='883');p.add_argument('--wizard',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args()
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));st=syntakt.dsp_image(str(ROOT/'firmware/Syntakt_OS1.42.syx'))
 tiny=json.loads((ROOT/'firmware/tiny-catalogue.json').read_text());wiz=json.loads((ROOT/'firmware/wizard-catalogue.json').read_text())
 masks=range(256,1024) if a.masks=='all' else [int(x) for x in a.masks.split(',')]
 for mask in masks:
  out=ROOT/'build/machine-combinations';out.mkdir(exist_ok=True)
  target=out/(str(mask)+('-w' if a.wizard else '-n')+'.json')
  if a.resume and target.exists() and not a.check:continue
  entry=generate(stock,st,tiny,wiz,mask,a.wizard)
  text=json.dumps(entry,separators=(',',':'))
  if a.check:assert target.read_text(encoding='utf-8')==text,target
  else:target.write_text(text,encoding='utf-8')
  print('ok',mask,a.wizard,entry['engine']['machine_names'],flush=True)
if __name__=='__main__':main()


