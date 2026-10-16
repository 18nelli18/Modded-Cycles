"""Choix page/boucle, ajouté sans déplacer les routines ni leurs hooks publics."""
import json,pathlib,copy,struct,subprocess,hashlib
import build,sprites,ref_mainos
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/genie-queue-choice');stock=load_stock('firmware/model-cycles_OS1.13.syx');data=json.load(open('work/sample-wizard-options/data.json'))
base=[data['sg']]+[t for t in json.load(open('work/sample-wizard-options/case-main-controls-without-wizard.json'))['tweaks'] if t['id'].startswith('scale-gen')]
slots=[(0x4016844c,96,'.text.avq_rows'),(0x40167aba,90,'.text.avq_boundary'),(0x40182c58,88,'.text.avq_value'),(0x4015fb80,88,'.data.avq')]
result={}
for index,old in enumerate(base):
 t=copy.deepcopy(old);s={k:int(v,16) for k,v in t['symbols'].items()}
 def get(at,n):
  w=next(w for w in t['writes'] if w['off']+build.BASE<=at and at+n<=w['off']+build.BASE+len(bytes.fromhex(w['new'])));i=at-w['off']-build.BASE;return w,i,bytes.fromhex(w['new'])[i:i+n]
 def patch(at,was,now):
  assert len(was)==len(now);w,i,b=get(at,len(was));assert b==was,(hex(at),b.hex(),was.hex());v=bytearray.fromhex(w['new']);v[i:i+len(was)]=now;w['new']=v.hex()
 hook=s['sg_q_hook'];w,_,body=get(hook,236);needle=bytes.fromhex('4a30080067064ef9');at=body.index(needle)+hook;out=int.from_bytes(body[at-hook+8:at-hook+12],'big');phase=at+12
 value=s['sg_advanced_value'];_,_,b=get(value,96);string=int.from_bytes(b[-4:],'big');assert b[-6:-4]==b'\x4e\xf9'
 defs={'Q_PHASE':phase,'Q_OUT':out,'VALUE_CONT':value+6,'STRING_CONT':string}
 (P/'link.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { '+''.join(sec+' '+hex(at)+' : { *('+sec+') } ASSERT(SIZEOF('+sec+') <= '+str(cap)+', "cave pleine") ' for at,cap,sec in slots)+' }')
 subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(P/'choice.o'),str(P/'choice.s')],check=True)
 subprocess.run(['m68k-elf-ld','-T',str(P/'link.ld'),'-o',str(P/'choice.elf'),str(P/'choice.o')],check=True)
 sy={r[2]:int(r[0],16) for l in subprocess.check_output(['m68k-elf-nm',str(P/'choice.elf')],text=True).splitlines() if len(r:=l.split())==3}
 for name,new in [('sg_map_row','avq_map'),('sg_unmap_row','avq_unmap')]:
  a=s[name];_,_,was=get(a,6);assert was[:2]==b'\x4e\xf9';patch(a,was,b'\x4e\xf9'+struct.pack('>I',sy[new]))
 patch(s['sg_ui_last'],bytes.fromhex('70144e75'),bytes.fromhex('70154e75'))
 patch(at,body[at-hook:at-hook+12],b'\x4e\xf9'+struct.pack('>I',sy['avq_boundary'])+b'\x4e\x71'*3)
 patch(value,bytes.fromhex('20035b80e988'),b'\x4e\xf9'+struct.pack('>I',sy['avq_value']))
 fields=s['sg_fields']+14*16;_,_,was=get(fields,16);patch(fields,was,struct.pack('>4I',sy['avq_mode'],0,1,0))
 for name in ['sg_labels','sg_stock_labels']:
  if name in s:
   a=s[name]+19*4;_,_,was=get(a,4);patch(a,was,struct.pack('>I',sy['avq_label']))
 for va,cap,section in slots:
  subprocess.run(['m68k-elf-objcopy','-O','binary','--only-section='+section,str(P/'choice.elf'),str(P/'choice.bin')],check=True);code=(P/'choice.bin').read_bytes();assert len(code)<=cap
  owner=next(w for w in t['writes'] if w['off']+build.BASE+len(bytes.fromhex(w['new']))==va)
  for path in pathlib.Path('work/sample-wizard-options').glob('case-*.json'):
   for other in json.load(open(path))['tweaks']:
    for w in other['writes']:assert not(va<w['off']+build.BASE+len(bytes.fromhex(w['new'])) and w['off']+build.BASE<va+len(code)),(path,other['id'])
  owner['new']+=code.hex();owner['old']=stock[owner['off']:owner['off']+len(bytes.fromhex(owner['new']))].hex()
 t['symbols'].update({k:hex(v) for k,v in sy.items() if k.startswith('avq_')});t['status']='experimental';t['description']+=' Choix Queue at : prochaine page de 16 pas ou boucle entière.'
 result['wizard' if index==0 else 'main']=t
 build.apply_writes(stock,[t],check_old=False) if False else None
 print('PASS',index,t['id'],'four existing freed-mask tails')
(P/'recipes.json').write_text(json.dumps(result))
(P/'refs.json').write_text(json.dumps({k:dict(w=hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest()) for k,t in result.items()}))
