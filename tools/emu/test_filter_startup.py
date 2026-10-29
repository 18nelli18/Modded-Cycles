"""Regression native : LOW differe, chargements sauvegardes et clear/Undo."""
from pathlib import Path
import argparse,inspect,json,sys
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'tools/emu'),str(R/'tools')]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
bc.ROOT=a.output.parent/'filter-context'
import test_fx_menu_control as fx
original_boot=bc.boot
fixture_source=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata')
exec(fixture_source,fx.__dict__)
original=(R/'tools/emu/test_filter_defaults.py').read_text()
original=original.replace("m=json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text())",'m=metadata')
prefix=original.split('for track in range(6):')[0]
rows=[]
for folder in a.build:
 meta=json.loads((folder/'BUILD.json').read_text());fx.metadata=meta
 fx.boot=lambda path:original_boot(next(folder.glob('*.syx')))
 def fresh():
  ns={'__file__':str(R/'tools/emu/test_filter_defaults.py'),'metadata':meta};old=sys.argv
  try:sys.argv=['test','v211'];exec(compile(prefix,'filter-fixture','exec'),ns)
  finally:sys.argv=old
  return ns
 # La suite historique execute clear, Undo, sauvegarde et chargement reels.
 ns={'__file__':str(R/'tools/emu/test_filter_defaults.py'),'metadata':meta};old=sys.argv
 try:sys.argv=['test','v211'];exec(compile(original,'filter-defaults-regression','exec'),ns)
 finally:sys.argv=old
 saved=[1,2,3,1,2,3]
 def prefs(n):n['f']['/Filter.cfg']=bytes([70,67,1,6,*saved,*[(~x)&255 for x in saved],165,90])
 for missing in ('root','handles'):
  n=fresh();prefs(n);r=n['r'];root=n['root'];raw=n['raw'];u=r.u
  if missing=='root':r.w32(0x40fe4228,0)
  else:
   for t in range(6):r.w32(n['handle'](t),0)
  for t in range(6):r.call(0x400141d2,raw(t))
  if missing=='root':r.w32(0x40fe4228,root)
  else:
   for t in range(6):r.w32(n['handle'](t),n['vt'])
  assert [r.call(0x468d0110,t) for t in range(6)]==[0]*6
  assert [n['filters'](t) for t in range(6)]==[(0x7f00,0)]*6
  print('PASS deferred LOW across six tracks with missing '+missing,flush=True)
 # Un buffer reutilise par le lecteur natif ne doit plus etre traite comme neuf.
 n=fresh();prefs(n);r=n['r'];raw=n['raw'];r.w32(0x40fe4228,0)
 for t in (0,1,2):r.call(0x400141d2,raw(t))
 r.call(0x400618f2,raw(1),13)
 r.w32(0x40fe4228,n['root'])
 assert [r.call(0x468d0110,t) for t in range(6)]==[0,saved[1],0,*saved[3:]]
 print('PASS saved sound initializer cancels only its pending reset',flush=True)
 # Le service UI resout aussi avant la lecture paresseuse des preferences.
 n=fresh();prefs(n);r=n['r'];r.w32(0x40fe4228,0);r.call(0x400141d2,n['raw'](4));r.w32(0x40fe4228,n['root'])
 r.call(0x468d0020)
 assert [r.call(0x468d0110,t) for t in range(6)]==[0 if t==4 else saved[t] for t in range(6)]
 print('PASS UI frame resolves pending reset without changing other saved tracks',flush=True)
 rows.append(dict(build=str(folder),sha256=meta['sha256'],six_tracks_root_missing=True,six_tracks_handles_missing=True,saved_load_cancels_pending=True,ui_frame_resolves=True,native_clear_undo_and_saved_startup=True))
a.output.write_text(json.dumps(dict(cases=rows,hardware_tested=False),indent=2)+'\n')
