"""Combinaisons réellement sélectionnables : machines indépendantes de Wizard.

La passerelle commune reste liée au même plan SRAM ; seuls les moteurs
sélectionnés reçoivent une entrée de machine. Sans moteur Syntakt, aucun
fragment de son OS n'est incorporé et son fichier n'est pas demandé.
"""
import pathlib,runpy,json,copy,struct,itertools
import build
P=pathlib.Path('work/sample-wizard-options');D=runpy.run_path('work/sample-wizard-main/engines.py');globals().update({k:D[k] for k in ['gs','gw','stock','st','ctx','sy','wizard','known','br','lay','gm','ga']})
allcodes=tuple(gs.CATALOG);gs.generation=lambda codes:allcodes
wave_cache={};variants={}
# Les gardes an.patches ne portent que sur les octets extraits du Syntakt.
an=gs.analyse(st,allcodes);st_relocs={int(x[0]) for x in an['patches']}
for mask in range(256):
 codes=tuple(c for i,c in enumerate(allcodes) if mask&(1<<i));macro,acid,wave_on=[bool(mask&(1<<i)) for i in [5,6,7]]
 if not mask:
  variants[str(mask)]=dict(wizard=copy.deepcopy(wizard),engine=None,wave=None);continue
 machines=[];parts=[]
 for selected,label,meta,at,up,rnd in [(macro,'MACRO',gm.MACHINE,0x46742000,'macro_update','macro_render'),(acid,'ACID',ga.MACHINE,0x46776000,'acid_update','acid_render')]:
  if not selected:continue
  parts.append(copy.deepcopy(next(p for p in known['append']['parts'] if int(p['dest'],16)==at and 'hex' in p)));machines.append(dict(meta,label=label,update=int(known['symbols'][up],16),render=int(known['symbols'][rnd],16)))
 wave=None
 if wave_on:
  index=7+len(codes)+len(machines)
  if index not in wave_cache:wave_cache[index]=gw.wave_part(0x46779000,0x4677b000,index,0x4677b000)
  wave=wave_cache[index];parts += [dict(dest=hex(at),hex=b.hex()) for at,b in wave['blobs']];machines.append(wave['machine'])
 own=dict(machines=machines,bridge=br,end=0x4677b3d0,boot2=((lay['end']+15)&~15,0x46742000),parts=parts)
 engine,_=gs.build_tweak(stock,st,codes,tg=ctx,own=own);engine.update(id='wizard-machines-'+str(mask),requires=['sample-wizard'],conflicts=[],status='experimental',prototype_only=False,flashable=True)
 if not codes:
  engine['append'].pop('syntakt',None);engine['append']['parts']=[p for p in engine['append']['parts'] if 'syntakt' not in p]
  engine['append']['reloc']=[r for r in engine['append']['reloc'] if int(r[0],16) not in st_relocs]
 engine['append']['compress_cost']=128
 w=copy.deepcopy(wizard)
 if wave:
  g=wave['gsyms'];raw=bytearray.fromhex(w['append']['parts'][0]['hex']);base=int(w['append']['dest'],16)
  for symbol,value in [('av_wave_tick',g['wt_tick']),('av_wave_note',g['wt_note']),('av_wave_yes',g['wt_yes']),('av_wave_machine',index)]:struct.pack_into('>I',raw,sy[symbol]-base,value)
  w['append']['parts'][0]['hex']=raw.hex();owned=[(x['off'],x['off']+len(x['new'])//2) for x in w['writes']+engine['writes']]
  engine['writes'] += [x for x in gw.wave_writes(stock,g) if not any(x['off']<hi and lo<x['off']+len(x['new'])//2 for lo,hi in owned)]
 # Une seule recette porte les écritures OS fusionnées avec leurs gardes stock.
 im,_=build.apply_writes(stock,[w,engine]);spans=[]
 for lo,hi in sorted((x['off'],x['off']+len(x['new'])//2) for x in w['writes']+engine['writes']):
  if spans and lo<=spans[-1][1]:spans[-1][1]=max(hi,spans[-1][1])
  else:spans.append([lo,hi])
 w['writes']=[dict(off=lo,old=stock[lo:hi].hex(),new=im[lo:hi].hex()) for lo,hi in spans];engine['writes']=[];w.update(prototype_only=False,flashable=True,status='experimental')
 variants[str(mask)]=dict(wizard=w,engine=engine,wave=dict(gsyms=wave['gsyms'],index=index) if wave else None)
 if mask%16==15:
  (P/'variants.json').write_text(json.dumps(variants));print('PASS combinaisons machines',mask+1,'/256',flush=True)
(P/'variants.json').write_text(json.dumps(variants));print('PASS 256 sélections machines ; aucune extraction Syntakt lorsque décoché.',flush=True)
