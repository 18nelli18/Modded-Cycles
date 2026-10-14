#!/usr/bin/env python3
"""Prototype privé 909/ACID : six emplacements stock remplacés, TG maintenu.

BD, SD, toms et rim/clap modélisés ; aucun sample de hats/cymbales.
"""
import argparse,json,pathlib,struct,tempfile
import build,gen_model909_additive as g9,gen_acid as ga,gen_macro as gm,gen_syntakt_engines as gs,gen_sdvintage_7th as g7
SLOTS=[('BD909','bd',0),('SD909','sd',1),('LT909','tom',3),('RC909','rc',2),('MT909','tom',3),('HT909','tom',3)]
def generate(stock,t,sample_capacity=0):
 tg=g9.context(stock,t);gs.set_base(gs.PAY_TG);pay=gs.PAY_TG
 with tempfile.TemporaryDirectory() as d:
  tmp=pathlib.Path(d);drum,ds,de=g9.compile_machine(tmp,pay,tg,stock_slots=True)
  at=pay+0x76000;bss=pay+0x80000
  acid,asym,ae=ga.compile_machine(tmp,at,ga.tables_header(),bss,bss)
  assert de<at
  cur=bytearray(tg['img']);extra=[]
  for i,(_,pre,_) in enumerate(SLOTS):
   for tab,kind in [(g7.UPDATE_TAB,'update'),(g7.RENDER_TAB,'render')]:
    va=tab+4*i;old=bytes(cur[va-build.BASE:va-build.BASE+4]);new=struct.pack('>I',ds[f't9_{pre}_{kind}']);cur[va-build.BASE:va-build.BASE+4]=new;extra.append(dict(off=va-build.BASE,old=old.hex(),new=new.hex()))
  tg['img']=bytes(cur)
  writes,ap=gm.added_machine(stock,tg,[dict(ga.MACHINE,label='ACID',update=asym['acid_update'],render=asym['acid_render'])],tmp,[(pay,drum),(at,acid)],ae)
  # Six noms propres dans la table commune de huit machines ; les callbacks
  # stock restent dans l’OS mais plus aucune entrée de machine ne les invoque.
  strings=bytearray();addresses={}
  def string(text):
   if text not in addresses:addresses[text]=pay+0x74000+len(strings);strings.extend(text.encode()+b'\0')
   return addresses[text]
  for name,_,_ in SLOTS:string(name)
  for _,_,m in SLOTS:
   for knob in g9.MACHINES[m][2]:string(knob[0]);string(knob[1])
  strings.extend(bytes(-len(strings)%4));str_at=pay+0x74000;assert str_at+len(strings)<at
  data=next(p for p in ap['parts'] if p['dest']==hex(gs.DATA));blob=bytearray.fromhex(data['hex']);pos=str_at
  for i,(name,_,_) in enumerate(SLOTS):struct.pack_into('>I',blob,4*i,addresses[name])
  data['hex']=blob.hex();ap['parts'].append(dict(dest=hex(str_at),hex=strings.hex()))
  for slot,(_,_,machine) in enumerate(SLOTS):
   for k,knob in enumerate(g9.MACHINES[machine][2]):
    long_,short,default,*limits=knob;lo,hi=limits if limits else (0,127)
    if machine==3 and k==1:default={2:0,4:1,5:2}[slot]
    index=(46+5*slot+k)*g7.DSTRIDE
    for off,value in [(8,lo<<8),(12,hi<<8),(16,default<<8),(44,addresses[long_]),(52,addresses[short])]:
     target=gs.DESCN+index+off;old=stock[g7.DESC+index+off-build.BASE:g7.DESC+index+off-build.BASE+4].hex();ap['reloc'].append([hex(target),old,struct.pack('>I',value).hex()])
  if sample_capacity:
   assert sample_capacity%4==0 and 0<sample_capacity<=180000
   assert pay+0x40000+sample_capacity<str_at
   ap['parts'].append(dict(dest=hex(pay+0x40000),hex='00'*sample_capacity))
  ap['pack']=[[hex(a),n] for a,n in gs.segments(ap['parts'],ap['size'])]
  # Le stub PACK doit être régénéré avec le segment de noms supplémentaire.
  (tmp/'segs.inc').write_text(''.join(f'\t.long\t{int(a,16):#x}, {n//4}\n' for a,n in ap['pack']))
  stub,_=gm.assemble(tmp,'stub909',gm.gx.SRC/'stub.S',gm.gx.CAVE,[f'-DPAYLOAD_SRC={int(ap["at"],16):#x}',f'-DPAYLOAD_DST={pay:#x}',f'-DPAYLOAD_LONGS={ap["size"]//4}','-DPACK',f'-I{tmp}',f'-DCHAIN_TO={tg["boot_extra_hook"]:#x}'])
  w=next(w for w in writes if w['off']==gm.gx.CAVE-build.BASE);w.update(old='ff'*len(stub),new=stub.hex())
 out=dict(id='model909-acid-replacement-tg',order=34,status='experimental',requires=[t['id']],conflicts=['chord-keys','chord-keys-supermodel'],writes=sorted(writes+extra,key=lambda w:w['off']),append=ap,symbols={k:hex(v) for k,v in {**ds,**asym}.items()},replacement_slots=[n for n,_,_ in SLOTS],source={'model909':'12e359160132fe7df4560ee3e53bd50ab9eebd2b','license':'MIT'},pending=['préservation des descripteurs Sampler partagés','preuves DSP/boot/ensemble','intégration flasher'])
 if sample_capacity:out['sample_slots']={'table':hex(ds['samples']),'pool':hex(pay+0x40000),'capacity':sample_capacity,'rate':32000}
 build.apply_writes(stock,[t,out]);return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cycles',required=True);p.add_argument('--tg-recipe',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=generate(g7.cycles_main(a.cycles),json.loads(pathlib.Path(a.tg_recipe).read_text()));pathlib.Path(a.output).write_text(json.dumps(out,indent=1)+'\n');print('Prototype compilé : six entrées 909, Sampler TG, ACID ; non publiable avant preuves/UI')
