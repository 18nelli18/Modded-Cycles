"""Note 108 : six voix 909 dans le profil Sample Wizard/ACID courant.
Code propre seulement, descripteurs OS extraits au build utilisateur.
"""
import argparse,copy,json,pathlib,struct,tempfile
import build,gen_model909_additive as g9,gen_macro as gm,gen_syntakt_engines as gs,gen_sdvintage_7th as g7
ROOT=pathlib.Path(__file__).resolve().parents[1];PAY=0x46700000
SLOTS=[('BD909','bd',0),('SD909','sd',1),('HATS909','hh',4),('RC909','rc',2),('TOM909','tom',3),('CYM909','cy',5)]
def generate():
 data=json.loads((ROOT/'build/909-current/scaffold.json').read_text());ts=data['tweaks'];combined_wizard=next(t for t in ts if t['id']=='sample-wizard');wizard=data['plainWizard'];base=next(t for t in ts if t.get('append',{}).get('dest')==hex(PAY));t=copy.deepcopy(base);ap=t['append'];gs.set_base(PAY)
 # Le catalogue partiel range ses hooks moteurs chez Wizard ; les separer
 # avant le composeur MIDI actuel, sans changer les octets finaux du profil.
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));plain,_=build.apply_writes(stock,[wizard])
 t['writes']=[dict(off=w['off'],old=bytes(plain[w['off']:w['off']+len(w['new'])//2]).hex(),new=w['new']) for w in combined_wizard['writes'] if bytes(plain[w['off']:w['off']+len(w['new'])//2]).hex()!=w['new']]+t['writes']
 g9.SRC=ROOT/'tools/machines/model909_full';g9.MACHINES=g9.MACHINES[:4]+[('HATS909','hh',(('HH Tone','TONE',64),('HH Type','TYPE',0,0,1),('HH Bits','BITS',0),('HH None','----',0))),('CYM909','cy',(('Cym Tone','TONE',64),('Cym Type','TYPE',0,0,1),('Cym Bits','BITS',0),('Cym None','----',0)))]
 old_bss=gm.BSS_OFF
 try:
  gm.BSS_OFF=0x3a000
  with tempfile.TemporaryDirectory() as d:body,sy,end=g9.compile_machine(pathlib.Path(d),PAY+0x9000,{'ah_noenv':int(wizard['symbols']['ah_noenv'],16)},stock_slots=True)
 finally:gm.BSS_OFF=old_bss
 assert end<=PAY+0x48000 and PAY+0x9000+len(body)<PAY+0x20000
 def part(at,raw):
  for p in ap['parts']:
   lo=int(p['dest'],16);n=len(p['hex'])//2 if 'hex' in p else int(p['cycles'][1],16)-int(p['cycles'][0],16)
   assert not (lo<at+len(raw) and at<lo+n),('collision',hex(at),hex(lo))
  ap['parts'].append({'dest':hex(at),'hex':raw.hex()})
 part(PAY+0x9000,body);part(PAY+0x48000,bytes(180000));strings=bytearray();addresses={}
 def string(s):
  if s not in addresses:addresses[s]=PAY+0x74000+len(strings);strings.extend(s.encode()+b'\0')
  return addresses[s]
 table=next(p for p in ap['parts'] if p['dest']==hex(PAY+0x33800));raw=bytearray.fromhex(table['hex']);nm=8
 for i,(name,pre,machine) in enumerate(SLOTS):
  struct.pack_into('>I',raw,4*i,string(name))
  for off,kind,native in [(4*nm,'update',g7.UPDATE_TAB),(8*nm,'render',g7.RENDER_TAB)]:
   target=sy[f't9_{pre}_{kind}'];struct.pack_into('>I',raw,off+4*i,target)
   old=stock[native+4*i-build.BASE:native+4*i-build.BASE+4]
   assert not any(w['off']<=native+4*i-build.BASE<w['off']+len(w['new'])//2 for w in t['writes'])
   t['writes'].append(dict(off=native+4*i-build.BASE,old=old.hex(),new=struct.pack('>I',target).hex()))
  for k,knob in enumerate(g9.MACHINES[machine][2]):
   long_,short,default,*limits=knob;lo,hi=limits if limits else (0,127)
   if machine==3 and k==1:default=1
   index=(46+5*i+k)*g7.DSTRIDE
   for off,value in [(8,lo<<8),(12,hi<<8),(16,default<<8),(44,string(long_)),(52,string(short))]:
    at=PAY+0x34000+index+off;old=stock[g7.DESC+index+off-build.BASE:g7.DESC+index+off-build.BASE+4].hex();new=struct.pack('>I',value).hex()
    ap['reloc']=[r for r in ap['reloc'] if int(r[0],16)!=at];ap['reloc'].append([hex(at),old,new])
 table['hex']=raw.hex();strings+=bytes(-len(strings)%4);part(PAY+0x74000,strings);assert PAY+0x74000+len(strings)<PAY+0x76000
 ap.pop('compressed_hex',None);t.update(id='model909-wizard-acid',name='909 kit + ACID with Sample Wizard',description=['Six slots 909 sur Sample Wizard courant, ACID main conserve. Aucun Model-TG installe. Nouvelle combinaison experimentale ; note 108.'],status='experimental',requires=['sample-wizard'],conflicts=[],symbols={k:hex(v) for k,v in sy.items()},sample_slots={'table':hex(sy['samples']),'pool':hex(PAY+0x48000),'capacity':180000,'rate':32000},replacement_slots=[x[0] for x in SLOTS]);t['writes'].sort(key=lambda w:w['off']);assert ap['size']>=0x74000+len(strings)
 build.apply_writes(stock,[wizard,t])
 return dict(engine=t,wizard=wizard,original_wizard_ref=data['refs']['sample-wizard'],original_id=base['id'],original_ref=data['refs'][base['id']],features=data['features'],bss_end=hex(end),startup=next(t for t in json.loads((ROOT/'docs/flasher-supermodel-909/profile.js').read_text().split('=',1)[1].strip().rstrip(';'))['tweaks'] if t['id']=='supermodel-909-startup'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();target=ROOT/'build/909-current/engine-data.js';text='window.MC909CurrentData='+json.dumps(generate(),separators=(',',':'))+';\n'
 if a.check:assert target.read_text()==text
 else:target.write_text(text)
 print('PASS 909 / Wizard : six slots, ACID main, 180000 octets samples, aucun Model-TG')
if __name__=='__main__':main()
