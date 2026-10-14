#!/usr/bin/env python3
"""ChordKeys PR87 MIT : placement compatible avec le catalogue Supermodel.

Les sources épinglées viennent de 18nelli18, PR87, 770369210cab889fd8642184632d7b9853afd33e.
La réserve de fichiers TG reste nulle ; les autres symboles TG restent fixes.
--layout JSON [{at,capacity,kind}] ; kind 'bank' ou 'sprite'.
"""
import argparse,copy,json,pathlib,struct,hashlib
import build,sprites,chord_keys_pr87 as ck,aplib_dense,aplib_cost
PIN='770369210cab889fd8642184632d7b9853afd33e'

def generate(stock,layout=None,tg=None,bank=None,prebuilt=None):
 if layout is None:
  # Générateur amont épinglé, catalogue local non parcouru : le placement
  # standalone est vérifié séparément de la variante Model-TG.
  compiled,syms=ck.compile_code()
 else:
  layout=[dict(x,at=int(x['at'],0) if isinstance(x['at'],str) else x['at']) for x in layout]
  for x in layout:
   if x['kind']=='bank':
    assert bank and bank['ram_only_rollback'] and bank['midi_reclaim']
    assert any(int(lo,16)<=x['at'] and x['at']+x['capacity']<=int(hi,16) for lo,hi in bank['midi_reclaim']['free_spans'])
   else:assert x['kind']=='sprite' and x['capacity']==sprites.MASKS[x['at']][0]
  if prebuilt:
   from chord_keys_relocate import relocate
   compiled,syms,audit=relocate(prebuilt,layout)
   from chord_keys_slot26 import adapt
   compiled,slot_audit=adapt(compiled,syms)
  else:
   assert all(x['kind']=='sprite' for x in layout),'placement mixte : recette MIT épinglée requise'
   ck.MASKS=tuple(x['at'] for x in layout);compiled,syms=ck.compile_code()
 writes=[];reservations=[];newbank=copy.deepcopy(bank)
 for addr,code in compiled:
  row=next((x for x in layout or [] if x['at']==addr),None)
  if row and row['kind']=='bank':
   part=newbank['append']['parts'][0];raw=bytearray.fromhex(part['hex']);off=addr-int(part['dest'],16)
   assert raw[off:off+len(code)]==bytes(len(code))
   raw[off:off+len(code)]=code;part['hex']=raw.hex()
   reservations.append(dict(at=hex(addr),size=len(code)))
  else:
   capacity,pointer,_,shared=sprites.MASKS[addr]
   assert stock[addr-build.BASE:addr-build.BASE+capacity]==stock[shared-build.BASE:shared-build.BASE+capacity]
   writes.extend([dict(off=addr-build.BASE,old=stock[addr-build.BASE:addr-build.BASE+len(code)].hex(),new=code.hex()),sprites.redirect_write(addr)])
 for addr,expected,symbol,opcode in ck.HOOKS:
  old=bytes.fromhex(expected);assert stock[addr-build.BASE:addr-build.BASE+len(old)]==old
  new=struct.pack('>I',syms[symbol]) if opcode is None else struct.pack('>HI',opcode,syms[symbol])
  new+=b'\x4e\x71'*((len(old)-len(new))//2)
  writes.append(dict(off=addr-build.BASE,old=expected,new=new.hex()))
 for addr,expected,new in ck.PATCHES:
  assert stock[addr-build.BASE:addr-build.BASE+len(bytes.fromhex(expected))].hex()==expected
  writes.append(dict(off=addr-build.BASE,old=expected,new=new))
 t=dict(id='chord-keys-supermodel' if bank else 'chord-keys',order=45,name='ChordKeys compatible Model-TG',device='Model:Cycles',os='1.13',section=3,status='experimental',conflicts=[],requires=[bank['id']] if bank else [],chord_keys_upstream_commit=PIN,symbols={k:hex(v) for k,v in sorted(syms.items())},writes=sorted(writes,key=lambda w:w['off']),bank_reservations=reservations,description=['ChordKeys COLOR, SHAPE, HARMONY et MIDI CHORD de Nico Heuser ; intégration MIT 18nelli18 PR87.','Généré par tools/gen_chord_keys_compat.py ; adresses des mods Supermodel conservées.'])
 build.apply_writes(stock,[t])
 if bank:
  newbank['chord_keys_upstream_commit']=PIN
  raw=bytes.fromhex(newbank['append']['parts'][0]['hex'])
  packed=min([aplib_dense.pack(raw,depth=d) for d in (32,128,512)]+[aplib_cost.pack(raw,depth=d,lazy=True) for d in (128,512,2048)],key=len)
  newbank['append']['compressed_hex']=packed.hex()
  assert newbank['writes']==bank['writes'] and newbank['symbols']==bank['symbols']
 if prebuilt:
  t['relocation_audit']=audit;t['harmony_slot_audit']=slot_audit;t['harmony_slot']=26
  t['description'].append('HARMONY au slot RAM26, identifiant disque33 conservé ; profondeur audio LFO2 au slot32 intacte.')
 return t,newbank

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--layout');p.add_argument('--tg');p.add_argument('--bank');p.add_argument('--bank-output');p.add_argument('--prebuilt');p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 read=lambda path:json.loads(pathlib.Path(path).read_text()) if path else None
 t,bank=generate(ck.load_stock(a.cycles),read(a.layout),read(a.tg),read(a.bank),read(a.prebuilt))
 for path,obj in [(a.output,t),(a.bank_output,bank)]:
  if obj is None:continue
  assert path,'--bank-output requis';text=json.dumps(obj,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(path)
  if a.check:assert out.read_text()==text
  else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
 print('ok : ChordKeys '+str(len(t['writes']))+' écritures, '+str(len(t['bank_reservations']))+' réserves B')
if __name__=='__main__':main()
