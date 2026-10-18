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

def compile_core(tmp,repo,pay,bss_at=None,machine=6):
 obj=tmp/'mm.o';elf=tmp/'mm.elf';raw=tmp/'mm.bin';ld=tmp/'mm.ld'
 gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,'-std=c99',f'-DMM_MACHINE={machine}','-c',str(HERE/'machines/midi_machine/core.c'),'-o',str(obj)])
 live=tmp/'live.o'
 gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,'-c',str(HERE/'machines/midi_machine/live.S'),'-o',str(live)])
 ld.write_text(f'SECTIONS {{ .text {pay:#x} : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss : {{ *(.bss*) *(COMMON) }} mm_end = .; }}')
 gm.gx.run([gm.gx.CROSS+'ld','-T',str(ld),'-e','mm_update','-o',str(elf),str(obj),str(live)])
 gm.gx.run([gm.gx.CROSS+'objcopy','-O','binary','-R','.bss',str(elf),str(raw)])
 sy={x[2]:int(x[0],16) for line in gm.gx.run([gm.gx.CROSS+'nm',str(elf)]).splitlines() if len(x:=line.split())==3}
 sy.update(macro_update=sy['mm_update'],macro_render=sy['mm_render'])
 return raw.read_bytes(),sy,max(pay+gm.BSS_OFF+4,(sy['mm_end']+3)&~3)

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
