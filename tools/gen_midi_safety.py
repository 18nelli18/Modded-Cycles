"""Candidat local : routage MIDI isole, notes live uniques, Chord inactif leger.
Ne genere aucune page publiee ; compiler puis tools/test_midi_safety_firmware.js.
"""
import json,pathlib,tempfile,sys,re
import gen_midi_machine_core as core
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/midi-safety';out.mkdir(exist_ok=True)
 catalogue_text=(ROOT/'docs/flasher/catalogue.js').read_text(encoding='utf8')
 ck=dict(re.findall(r'"((?:ck_|chord_)[^"]+)":"(0x[0-9a-f]+)"',catalogue_text))
 assert 'ck_audio_config' in ck and 'chord_audio_original' in ck
 with tempfile.TemporaryDirectory() as folder:
  tmp=pathlib.Path(folder)
  blob,sy,end=core.compile_core(tmp,None,0x4678e000,machine=17,controls=True)
  # BSS doit etre inclus dans la reservation initialisee a zero au boot.
  assert sy['mm_end']<0x46794000
  data=dict(hex=blob.hex(),symbols={k:v for k,v in sy.items() if k.startswith('mm_')},end=sy['mm_end'],origin=0x4678e000)
  objs=[]
  for name in ('chord_audio.c',):
   obj=tmp/(name+'.o');core.gm.gx.run([core.gm.gx.CROSS+'gcc',*core.gm.gx.CFLAGS,'-std=c99','-I'+str(ROOT/'tools/machines/chord_keys_compat'),'-c',str(ROOT/'tools/machines/midi_safety'/name),'-o',str(obj)]);objs.append(str(obj))
  ld=tmp/'chord.ld';elf=tmp/'chord.elf';raw=tmp/'chord.bin'
  ld.write_text('SECTIONS { .text 0x46794000 : { *(.text*) *(.rodata*) } .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } chord_end = .; }\n'+''.join(f'{k} = {ck[k]};\n' for k in ck if k.startswith('ck_') or k=='chord_audio_original'))
  core.gm.gx.run([core.gm.gx.CROSS+'ld','-T',str(ld),'-e','chord_audio_update','-o',str(elf),*objs]);core.gm.gx.run([core.gm.gx.CROSS+'objcopy','-O','binary',str(elf),str(raw)])
  csy={x[2]:int(x[0],16) for l in core.gm.gx.run([core.gm.gx.CROSS+'nm',str(elf)]).splitlines() if len(x:=l.split())==3}
  data['chord']=dict(end=csy['chord_end'],origin=0x46794000,hex=raw.read_bytes().hex(),symbols=csy)
 import gen_midi_machine_catalogue as catalogue
 entry=catalogue.generate(1023,True,True)
 sites={site for site,_,_ in list(core.CONTROL_HOOKS)+list(core.LIVE_HOOKS)}
 entry['engine']['writes']=[w for w in entry['engine']['writes'] if w['off']+0x40000400 not in sites]
 entry['engine']['append']['parts'].append(dict(dest=hex(data['chord']['origin']),hex=data['chord']['hex']))
 entry['engine']['append']['size']=max(entry['engine']['append']['size'],data['chord']['end']-int(entry['engine']['append']['dest'],16))
 entry['engine']['append'].pop('compressed_hex',None);entry['engine']['append'].pop('stored',None)
 (out/'catalogue.json').write_text(json.dumps(entry,separators=(',',':'))+'\n',encoding='utf8')
 (out/'data.json').write_text(json.dumps(data,indent=1)+'\n',encoding='utf8')
 print('PASS modules locaux MIDI et Chord',len(blob),hex(sy['mm_end']),len(data['chord']['hex'])//2)
if __name__=='__main__':main()
