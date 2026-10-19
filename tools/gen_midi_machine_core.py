"""Prototype local machine MIDI : slot natif ajoute, silence et masque par piste.

Ne publie aucune page ; l'interface et les services MIDI ne sont pas encore
relies. La recette reste sous build ignore, jamais annoncee comme fonctionnelle.
"""
import argparse,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import build,gen_macro as gm,gen_syntakt_engines as gs,gen_sdvintage_7th as g7
ROOT=HERE.parent
MACHINE=dict(name='MIDI Out',image=4,decay=0,knobs=(('CC 1','CC1',64),('CC 2','CC2',64),('CC 3','CC3',64),('CC 4','CC4',64)))
LIVE_HOOKS=((0x40019ee2,'4e922f004eb94000f208','mm_key_on_hook'),(0x4001d094,'45f9400cf866','mm_pad_on_hook'),(0x40019cba,'2f044eb940016e90','mm_key_off_hook'),(0x4001d120,'45f9400cf866','mm_pad_off_hook'))

def compile_core(tmp,repo,pay,bss_at=None,machine=6,controls=False):
 obj=tmp/'mm.o';elf=tmp/'mm.elf';raw=tmp/'mm.bin';ld=tmp/'mm.ld'
 gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,'-std=c99',f'-DMM_MACHINE={machine}',*(['-DMM_CONTROLS=1'] if controls else []),'-c',str(HERE/'machines/midi_machine/core.c'),'-o',str(obj)])
 live=tmp/'live.o'
 gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,f'-DMM_MACHINE={machine}',*(['-DMM_CONTROLS=1'] if controls else []),'-c',str(HERE/'machines/midi_machine/live.S'),'-o',str(live)])
 objects=[str(obj),str(live)]
 if controls:
  for name in ('controls.c','ui.c','ui.S','track_menu.S','storage.c','storage.S','worker.c','worker.S','settings.c','lfo.c','lfo.S'):
   target=tmp/(name+'.o')
   gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,'-std=c99',f'-DMM_MACHINE={machine}','-c',str(HERE/'machines/midi_machine'/name),'-o',str(target)])
   objects.append(str(target))
  popup=tmp/'popup.s';popup.write_text((HERE/'machines/beat_repeat/popup.s').read_text().replace('br_popup','mm_popup'))
  target=tmp/'popup.o';gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,'-c',str(popup),'-o',str(target)]);objects.append(str(target))
 ld.write_text(f'SECTIONS {{ .text {pay:#x} : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss : {{ *(.bss*) *(COMMON) }} mm_end = .; }}')
 gm.gx.run([gm.gx.CROSS+'ld','-T',str(ld),'-e','mm_update','-o',str(elf),*objects])
 gm.gx.run([gm.gx.CROSS+'objcopy','-O','binary','-R','.bss',str(elf),str(raw)])
 sy={x[2]:int(x[0],16) for line in gm.gx.run([gm.gx.CROSS+'nm',str(elf)]).splitlines() if len(x:=line.split())==3}
 sy.update(macro_update=sy['mm_update'],macro_render=sy['mm_render'])
 return raw.read_bytes(),sy,max(pay+gm.BSS_OFF+4,(sy['mm_end']+3)&~3)

CONTROL_HOOKS=(
 (0x400775f8,'4fefffc048d70c04','mm_encoder_hook'),
 (0x4001b22a,'4e56ffc048d73cfc','mm_draw_hook'),
 (0x40077720,'4fefffa048d77cfc','mm_ui_key_hook'),
 (0x4005afa0,'4feffff448d71c00','mm_save2_hook'),
 (0x4005b054,'4feffff448d71c00','mm_save1_hook'),
 (0x4005aecc,'4feffff448d71c00','mm_load_hook'),
 (0x4008a0f0,'720126407113b280','mm_worker_hook'),
 (0x40082726,'487800012f2f000c','mm_note_route'),
 (0x4005919e,'42b940a78e18','mm_sequence_hook'),
 (0x40058f3c,'4fef000c60000262','mm_lock_only_hook'),
)
CONTROL_POINTERS=((0x40108138,'400426fa','mm_track_draw'),)

def connect_controls(stock,t,sy,prior=()):
 """Accroches autonomes ; le composeur doit chainer les detours deja occupes."""
 current=build.apply_writes(stock,list(prior))[0] if prior else stock
 storage={0x4005afa0:0,0x4005b054:1,0x4005aecc:2}
 for site,expected,name in CONTROL_HOOKS:
  off=site-build.BASE;size=len(expected)//2
  assert bytes(stock[off:off+size]).hex()==expected,(hex(site),'octets stock')
  assert not any(w['off']<off+size and off<w['off']+len(w['new'])//2 for w in t['writes']),(hex(site),'detour deja occupe')
  before=bytes(current[off:off+size])
  if before.hex()!=expected:
   assert site in storage and before[:2]==b'\x4e\xf9',(hex(site),'composition inconnue')
   at=sy['mm_storage_api']+4*storage[site]
   for part in t['append']['parts']:
    if 'hex' not in part:continue
    start=int(part['dest'],16);raw=bytearray.fromhex(part['hex'])
    if start<=at and at+4<=start+len(raw):
     assert raw[at-start:at-start+4]==bytes(4)
     raw[at-start:at-start+4]=before[2:6];part['hex']=raw.hex();break
   else:raise AssertionError('API storage hors charge utile')
  t['writes'].append(dict(off=off,old=before.hex(),new='4ef9'+sy[name].to_bytes(4,'big').hex()+'4e71'*((size-6)//2)))
 zones=[(site-build.BASE+2,site-build.BASE+len(old)//2) for site,old,_ in CONTROL_HOOKS]
 sure,branches=build.refs_into(stock,zones);assert not sure and not branches,(sure,branches)
 for site,old,name in CONTROL_POINTERS:
  off=site-build.BASE;assert bytes(current[off:off+4]).hex()==old
  t['writes'].append(dict(off=off,old=old,new=sy[name].to_bytes(4,'big').hex()))
 t['writes'].sort(key=lambda w:w['off'])

def connect_notes(stock,t,sy):
 """MOut automatique pour ce slot seulement ; autres pistes suivent le getter stock."""
 at=0x40016e90;off=at-0x40000400
 old=bytes(stock[off:off+6]);assert old.hex()=='2f0a246f0008'
 assert not any(w['off']<=off+5 and w['off']+len(bytes.fromhex(w['new']))>off for w in t['writes'])
 t['writes'].append(dict(off=off,old=old.hex(),new='4ef9'+int(sy['mm_mout']).to_bytes(4,'big').hex()))
 t['writes'].sort(key=lambda w:w['off'])
 for site,expected,name in LIVE_HOOKS:
  size=len(bytes.fromhex(expected))
  off=site-0x40000400
  assert bytes(stock[off:off+size]).hex()==expected,hex(site)
  assert not any(w['off']<=off+size-1 and w['off']+len(bytes.fromhex(w['new']))>off for w in t['writes'])
  new='4ef9'+int(sy[name]).to_bytes(4,'big').hex()+'4e71'*((size-6)//2)
  t['writes'].append(dict(off=off,old=bytes(stock[off:off+size]).hex(),new=new))
 t['writes'].sort(key=lambda w:w['off'])

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'))
 t,info=gm.build_tweak(stock,None,engine=dict(machine=MACHINE,compile=compile_core,symbols=('mm_update','mm_render','mm_mask','mm_mout','mm_mout_original','mm_live_on','mm_live_off','mm_key_on_hook','mm_pad_on_hook','mm_key_off_hook','mm_pad_off_hook')))
 connect_notes(stock,t,{k:int(v,16) for k,v in t['symbols'].items()})
 build.apply_writes(stock,[t])
 t.update(id='midi-machine-core',name='Prototype local machine MIDI',status='experimental',requires=[],conflicts=[],machine_names=['Kick','Snare','Metal','Perc','Tone','Chord','MIDI Out'])
 t['prototype_limits']=['Notes live natives raccordees ; CC, sequence complete, transitions, interface et persistance encore a prouver. Ne pas flasher comme produit fini.']
 path=ROOT/'build/midi-machine/core.json';path.parent.mkdir(exist_ok=True)
 text=json.dumps(t,separators=(',',':'))+'\n'
 if a.check:assert path.read_text()==text
 else:path.write_text(text)
 print('PASS recette locale MIDI Out index6, autres machines conservees ; integration MIDI encore requise')
if __name__=='__main__':main()
