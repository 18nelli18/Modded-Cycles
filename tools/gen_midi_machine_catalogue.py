"""Prototype MIDI ajoute aux moteurs existants ; bornes descripteurs32bits.

La selection complete passe de126 a131descripteurs : MOVEQ ne convient plus.
Les generateurs existants restent identiques sans l'argument extra.
Recettes locales seulement, services MIDI pas encore raccordes.
"""
import argparse,copy,json,pathlib,sys,tempfile
HERE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import gen_machine_combinations as combinations,gen_midi_machine_core as core
import gen_sdvintage_7th as g7,build,syntakt
ROOT=HERE.parent

def wide_bounds(stock,entry,pay):
 t=entry['engine'];base=build.apply_writes(stock,[entry['wizard']])[0] if 'wizard' in entry else stock
 at=pay+0x8d000;code=bytearray();changes=[];sites=[];ndesc=76+5*(len(t['machine_names'])-(7 if 'wizard' in entry else 6))
 if ndesc<=127:return
 for site in g7.BOUNDS:
  rows=[w for w in t['writes'] if w['off']==site-build.BASE]
  assert len(rows)==1,(hex(site),rows)
  if rows[0]['new'].startswith('4ef9') and len(rows[0]['new'])==12:continue
  assert len(rows[0]['new'])==4,(hex(site),rows)
  row=rows[0];raw=bytes(base[site-build.BASE:site-build.BASE+6]);reg=(raw[0]-0x70)//2
  assert raw[0]==0x70+2*reg and raw[1] in (75,76)
  value=int(row['new'][2:],16);assert value in (ndesc,ndesc-1)
  stub=at+len(code);code+=(0x203c+reg*0x200).to_bytes(2,'big')+value.to_bytes(4,'big')
  tail=raw[2:]
  if tail[2]&0xf0==0x60:
   condition=tail[2]&15;assert condition>=2 and tail[3] not in (0,255),(hex(site),tail.hex())
   delta=int.from_bytes(tail[3:4],'big',signed=True);target=site+6+delta
   code+=tail[:2]+bytes((0x60+(condition^1),6))+b'\x4e\xf9'+target.to_bytes(4,'big')
  else:code+=tail
  code+=b'\x4e\xf9'+(site+6).to_bytes(4,'big')
  t['writes'].remove(row);changes.append(dict(off=site-build.BASE,old=raw.hex(),new='4ef9'+stub.to_bytes(4,'big').hex()));sites.append(hex(site))
 assert at+len(code)<=pay+0x8e000
 t['writes'].extend(changes);t['writes'].sort(key=lambda w:w['off']);t['append']['parts'].append(dict(dest=hex(at),hex=code.hex()))
 t['wide_descriptor_bounds']=dict(count=ndesc,sites=sites,start=hex(at),size=len(code))
 build.apply_writes(stock,([entry['wizard']] if 'wizard' in entry else [])+[t])

def generate(mask,wizard,controls=False):
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));st=syntakt.dsp_image(str(ROOT/'firmware/Syntakt_OS1.42.syx'))
 tiny=json.loads((ROOT/'firmware/tiny-catalogue.json').read_text());wiz=json.loads((ROOT/'firmware/wizard-catalogue.json').read_text());pay=0x46700000
 with tempfile.TemporaryDirectory() as tmp:
  code=pay+(0x8e000 if controls else 0x8c000)
  blob,sy,end=core.compile_core(pathlib.Path(tmp),None,code,machine=6+int(wizard)+mask.bit_count(),controls=controls)
  reserve=pay+(0x92000 if controls else 0x8e000)
  assert sy['mm_end']<=reserve,(hex(sy['mm_end']),hex(reserve))
 extra=dict(machine=dict(core.MACHINE,label='MIDI',update=sy['mm_update'],render=sy['mm_render']),parts=[dict(dest=hex(code),hex=blob.hex())],end=reserve)
 out=combinations.generate(stock,st,tiny,wiz,mask,wizard,extra=extra)
 wide_bounds(stock,out,pay)
 core.connect_notes(stock,out['engine'],sy)
 if controls:core.connect_controls(stock,out['engine'],sy,([out['wizard']] if 'wizard' in out else []))
 build.apply_writes(stock,([out['wizard']] if 'wizard' in out else [])+[out['engine']])
 out['engine']['symbols']={k:hex(v) for k,v in sy.items() if k.startswith('mm_')}
 out['engine']['status']='experimental';out['engine']['id']='midi-machine-'+str(mask)+('-wizard' if wizard else '')
 out['engine']['prototype_limits']=(['Integration complete reservee au preset Select All de test ; verification materielle et profils partiels encore requis.'] if controls else ['Audio nul et notes live natives ; CC, sequence complete, transitions, interface et persistance encore a prouver.'])
 out.pop('engine_sha256',None)
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--mask',type=int,default=1023);p.add_argument('--wizard',action='store_true');p.add_argument('--controls',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
 data=generate(a.mask,a.wizard,a.controls)
 path=ROOT/'build/midi-machine'/f'catalogue-{a.mask}-{int(a.wizard)}{"-controls" if a.controls else ""}.json';path.parent.mkdir(exist_ok=True);text=json.dumps(data,separators=(',',':'))+'\n'
 if a.check:assert path.read_text()==text
 else:path.write_text(text)
 print('PASS catalogue local',data['engine']['machine_names'],data['engine'].get('wide_descriptor_bounds'))
if __name__=='__main__':main()
