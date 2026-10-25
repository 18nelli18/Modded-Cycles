"""Transfert natif Mod Setup -> MACHINES : regression128 et candidat129."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT
from test_keep_machine_params import fixture as machine_fixture
v=sys.argv[1] if len(sys.argv)>1 else 'v129'
stem='staging/all-features-polivoks-cpu-trim-test-'+v
m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());sy=m['symbols'];sx=m['scramble_mask']['symbols'];d=m['sidechain']['symbols']
r,s,h,log,files,oldkey,oldturn,data,bind=fixture(stem)
bind(m['scramble_mask']['original']['sc_steps_toggle'],lambda a:0)
def key(code,flags=1):
 raw=struct.pack('>6I',0x400fbebc,0,100,code,flags,127);r.u.mem_write(EVENT,raw)
 result=r.call(sy['wf_key'],EVENT)
 assert bytes(r.u.mem_read(EVENT,24))==raw
 return result
def open_menu():
 key(13);key(2);key(2,16);key(13,0)
 assert r.r32(sy['menu']) and not r.r32(sy['editing'])
def click():key(32);key(32,16)
delegate=0x931b0000;forward=[]
r.w32(sy['wf_api'],delegate)
bind(delegate,lambda a:forward.append(a[:2]) or 0x12345678)
def turn():
 r.delta=1;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,101,1,1,0))
 return r.call(sy['wf_encoder_hook'],0x1234,EVENT)
rows=['root','root-edit','scramble','sidechain','sidechain-edit','mute']
for page in rows:
 for release_settings_first in (False,True):
  open_menu()
  if page=='root-edit':click()
  elif page=='scramble':r.w32(sy['row'],6);click()
  elif page.startswith('sidechain') or page=='mute':
   r.w32(sy['row'],7);click();r.w32(d['du_row'],9 if page=='mute' else 5)
   if page=='sidechain-edit':click()
  if release_settings_first:key(13)
  before_row=r.r32(sy['row']);assert not forward
  ret=turn();assert ret==1 and not forward,(page,ret,forward,hex(r.r32(sy['wf_api'])))
  before=bytes(r.u.mem_read(d['du_config'],30))+bytes(r.u.mem_read(sx['sx_masks'],6))
  assert key(5)==0
  assert not r.r32(sy['menu']) and not r.r32(sy['editing'])
  assert not r.r32(sx['sx_submenu']) and not r.r32(d['du_page']) and not r.r32(d['du_edit'])
  assert not r.r32(sy['pending'])
  assert turn()==0x12345678 and forward==[(0x1234,EVENT)]
  forward.clear();key(5,9);key(5,33);key(5,16)
  if release_settings_first:key(13,0)
  assert not r.r32(sy['menu'])
  assert bytes(r.u.mem_read(d['du_config'],30))+bytes(r.u.mem_read(sx['sx_masks'],6))==before
  assert not r.r32(sy['settings']) and not r.r32(sy['track_owned'])
  open_menu();assert not r.r32(sx['sx_submenu']) and not r.r32(d['du_page'])
  key(12);key(12,16);assert not r.r32(sy['menu'])
print('PASS12 root/edit/Scramble/Sidechain/Mute transitions: real menu encoder hook delegates, key untouched, modifiers/reopen/BACK and settings preserved',flush=True)
# Nouveau MACHINES arrive apres un vrai appui, jamais sur une release/repetition seule.
for flags in (0,16,9,33):
 open_menu();key(5,flags);assert r.r32(sy['menu']);key(12);key(12,16)
assert key(5)==0 and not r.r32(sy['menu'])
open_menu();key(1);assert key(5,3)==0 and not r.r32(sy['menu']);key(5,2);key(1,0)
print('PASS only fresh MACHINES closes Mod Setup; native Machine and FUNC+Machine events remain available',flush=True)
# Execute le vrai gestionnaire de selection apres le transfert prouve ci-dessus.
u,obj,snd=machine_fixture(stem);this=0x93900000
u.uc.mem_map(0xfc070000,0x1000)
u.uc.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,101,1,1,0))
u.hooks[0x4006f6ce]=('data-encoder',1);u.hooks[0x4006f73a]=('delta',1);u.hooks[0x4007faf4]=('no-track-modifier',0)
for i in range(6):u.uc.mem_write(this+0x70+4*i,struct.pack('>i',-1))
u.uc.mem_write(snd,bytes(100));u.uc.mem_write(snd+38,b'\x00\x00')
ids=[]
for i in range(23):
 u.uc.mem_write(m['fx_menu']['symbols']['machine_valid'],bytes(4))
 u.call(0x400a28b4,this,EVENT)
 assert not u.bad,u.bad
 ids.append(u.uc.mem_read(snd+38,1)[0])
assert len(set(ids))==22 and 6 in ids and ids[-1]==17,ids
u.hooks[0x4006f73a]=('delta',0xffffffff)
u.uc.mem_write(m['fx_menu']['symbols']['machine_valid'],bytes(4));u.call(0x400a28b4,this,EVENT)
assert u.uc.mem_read(snd+38,1)[0]!=17 and not u.bad
print('PASS native DrumSelect EncoderEvent -> actual machine setter visits all23 machines, MIDI Out last, reverse works',flush=True)
from boot_candidate import boot
old='v128adult' if v.endswith('adult') else 'v128'
oldim,oldmem=boot(R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+old+'.syx'))
newim,newmem=boot(R/'output/firmware'/(stem+'.syx'))
lo=m['gesture_swap']['code'];hi=0x4684f000
a,b=oldmem[0][1],newmem[0][1];base=oldmem[0][0]
assert len(a)==len(b) and a[:lo-base]==b[:lo-base] and a[hi-base:]==b[hi-base:]
assert newim[:0x401aa140-0x40000400]==oldim[:0x401aa140-0x40000400]
print('PASS resident native code and full runtime unchanged outside the gesture UI region: audio, menus, storage, banks and voice behavior exact128',flush=True)
