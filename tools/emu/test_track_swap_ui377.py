"""Swap integre : vrais getters natifs, transactions et navigation MenuView."""
from pathlib import Path
import sys,json,struct,argparse,random
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
m=json.loads((a.build/'BUILD.json').read_text());d=m['track_swap377'];s=d['symbols'];al=d['aliases']
r=Rig((a.capture/'native.bin').read_bytes(),{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in s.items()}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,(a.capture/'runtime.bin').read_bytes())
calls=[];fx=bytearray(range(78));fx[42:72:5]=bytes([2,4,8,16,32,1]);filters=[0,1,2,3,0,1]
def bind(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
root,pat,kit,raw,sounds=0x42000000,0x42002000,0x42003000,0x4140001c,0x416cfc5c
vt,getter,notice,access=0x42030000,0x400d639e,0x42030100,0x42030200
bind(notice,lambda a:calls.append(('notify',a[0])) or 0)
bind(0x400cf866,lambda a:root);bind(0x4000f208,lambda a:pat);bind(0x4000eb9c,lambda a:kit)
bind(0x40009c1a,lambda a:kit+256+64*a[1])
for off in (16,40,52):r.w32(vt+off,notice if off==16 else getter)
r.w32(kit,vt);r.w32(kit+16,sounds);r.w32(pat+640,vt);r.w32(pat+656,raw+4332);r.w32(0x40a7887c,0x406fa040)
r.w32(0x406fa040+30706,0);r.w32(0x406fa02c,0)
r.w32(root,vt);r.w32(root+16,raw-28)
for t in range(6):
 for obj,data in [(pat+112+88*t,raw+722*t),(kit+256+64*t,sounds+28+100*t)]:r.w32(obj,vt);r.w32(obj+16,data)
for k in ['ts_mf_choose','ts_mf_capture']:bind(al[k],lambda a:calls.append(('service',a[:3])) or 0)
bind(al['ts_mf_choice'],lambda a:0)
def capture(args):u.mem_write(args[0],bytes(fx[:36]));return 0
def apply(args):
 fx[:]=u.mem_read(args[0],78)
 u.mem_write(al['ts_scramble_masks'],bytes(fx[36:42]));u.mem_write(al['ts_duck_config'],bytes(fx[42:72]));u.mem_write(al['ts_duck_fx'],bytes(fx[72:78]));return 0
bind(al['ts_fxp_capture'],capture);bind(al['ts_fxd_apply'],apply)
bind(al['ts_filter_get'],lambda a:filters[a[0]])
def set_filter(args):filters[args[0]]=args[1];return 0
bind(al['ts_filter_set'],set_filter);bind(0x40076bee,lambda a:0)
for t in range(6):
 u.mem_write(al['ts_scramble_masks']+t,bytes([36+t]));u.mem_write(al['ts_duck_config']+5*t,bytes([fx[42+5*t],1,2,3,t]));u.mem_write(al['ts_duck_fx']+t,bytes([t%3]))
r.w32(al['ts_lfo_context'],0x42025000)
for bank in range(2):r.w32(al['ts_extra_contexts']+4*bank,0x42026000+bank*0x1000)
extra=[]
for name in ['ts_lp_one','ts_lp_two']+(['ts_glide','ts_legato','ts_acid_initialized','ts_slot','ts_mode'] if m.get('edition')!='lite' else []):
 base=al[name]
 for t in range(6):r.w32(base+4*t,t+1)
 extra.append((base,4,4))
for base in [al['ts_extra_polarity'],al['ts_extra_polarity']+24]:
 for t in range(6):r.w32(base+4*t,t&1)
 extra.append((base,4,4))
for base in [0x42025000,0x42026000,0x42027000]:
 for t in range(6):
  u.mem_write(base+32*t,bytes([t+1])*32)
  u.mem_write(base+192+16*t,struct.pack('>8H',0x7000,0x400,0x4000+t*128,0x7f00,0,0,0,0x4000))
 extra.extend([(base,32,32),(base+192,16,16)])
xp=m['lfo_reload']['symbols'];mx=m['four_lfos']['symbols']
for sy,storage,where in [(xp,'storage',0x42100000),(mx,'mx_storage',0x42110000)]:
 r.w32(sy['ready'],1);r.w32(sy['current'],0);r.w32(sy[storage],where)
extra_before=[bytes(u.mem_read(base,stride*6)) for base,stride,size in extra]
rng=random.Random(377)
u.mem_write(raw,bytes(rng.randrange(256) for _ in range(30710)));u.mem_write(sounds,bytes(rng.randrange(256) for _ in range(628)))
r.w32(raw+30706,0)
for t in range(6):u.mem_write(sounds+16+2*t,struct.pack('>H',((t*23+7)%128)*256+17+t))
ck_words=None
if 'ts_ck_read' in al:
 cs=m['chord_storage300'];ca=cs['aliases'];cobj=0x42130000;r.w32(cobj,vt);r.w32(cobj+16,raw+30642)
 bind(ca['cs_object'],lambda a:cobj);bind(ca['cs_ui_header'],lambda a:raw+30642);bind(ca['cs_audio_header'],lambda a:raw+30642);bind(ca['cs_clear_modifiers'],lambda a:0)
 r.w32(raw+30674,0);ck_words=[]
 for t in range(6):
  word=0x80000000|(t<<28)|((24+t)<<21)|sum(((t+i)%5)<<(3*i) for i in range(7));ck_words.append(word);r.call(al['ts_ck_set'],t,word);r.call(al['ts_ck_midi_set'],t,int(t==1))
 u.mem_write(raw+30642+60,b'PL\x10\xef');calls.clear()
r.w32(al['ts_song'],2);u.mem_write(al['ts_song']+8,bytes([0,1,2,0,1,1,2,0]))
fx_before=bytes(fx[:36])+bytes(u.mem_read(al['ts_scramble_masks'],6))+bytes(u.mem_read(al['ts_duck_config'],30))+bytes(u.mem_read(al['ts_duck_fx'],6))
before=(bytes(u.mem_read(raw,30710)),bytes(u.mem_read(sounds,628)),list(filters))
other_patterns=bytes(u.mem_read(raw+30710,95*30710))
other_kits=bytes(u.mem_read(sounds+7094,95*7094))
assert r.call('ts_native_swap',1,4)==1
for t in range(6):
 source=4 if t==1 else 1 if t==4 else t
 assert bytes(u.mem_read(raw+722*t,722))==before[0][722*source:722*(source+1)]
 assert bytes(u.mem_read(raw+4332+4385*t,4385))==before[0][4332+4385*source:4332+4385*(source+1)]
 assert bytes(u.mem_read(sounds+28+100*t,100))==before[1][28+100*source:28+100*(source+1)]
 assert bytes(u.mem_read(sounds+16+2*t,2))==before[1][16+2*source:18+2*source]
 assert r.call(0x40009c5a,kit,t)&255==before[1][16+2*source]
 assert filters[t]==before[2][source]
assert len([x for x in calls if x[0]=='notify'])==(9 if ck_words else 5)
if ck_words:
 assert [r.call(al['ts_ck_read'],raw+30642,t) for t in range(6)]==[ck_words[4 if t==1 else 1 if t==4 else t] for t in range(6)]
 assert r.call(al['ts_ck_midi_get'],4)==1 and r.call(al['ts_ck_midi_get'],1)==0
 assert bytes(u.mem_read(raw+30642+60,4))==b'PL\x10\xef'
assert u.mem_read(al['ts_song']+10,1)==b'\x10' and u.mem_read(al['ts_song']+14,1)==b'\2'
for t in range(6):
 source=4 if t==1 else 1 if t==4 else t
 mask=fx_before[42+5*source];different=((mask>>1)^(mask>>4))&1
 assert fx[42+5*t]==mask^(different<<1)^(different<<4)
for (base,stride,size),old in zip(extra,extra_before):
 for t in range(6):
  source=4 if t==1 else 1 if t==4 else t
  assert bytes(u.mem_read(base+stride*t,size))==old[stride*source:stride*source+size]
assert bytes(u.mem_read(0x42100000+16+96*116,96))==bytes(u.mem_read(0x42025000+192,96))
assert bytes(u.mem_read(0x42110000,96))==bytes(u.mem_read(0x42026000+192,96))
assert bytes(u.mem_read(0x42110000+96,96))==bytes(u.mem_read(0x42027000+192,96))
print('PASS moved LFO settings/phases, ACID and Wizard caches; actual LFO2/3/4 capture functions publish swapped settings into saved pattern banks')
assert r.call('ts_native_swap',1,4)==1
assert bytes(u.mem_read(raw,30710))==before[0] and bytes(u.mem_read(sounds,628))==before[1] and filters==before[2]
assert bytes(fx)==fx_before and u.mem_read(al['ts_song']+10,1)==b'\2'
assert bytes(u.mem_read(raw+30710,95*30710))==other_patterns
assert bytes(u.mem_read(sounds+7094,95*7094))==other_kits
state=(bytes(u.mem_read(raw,30710)),bytes(u.mem_read(sounds,628)))
r.w32(root+16,0x41800000)
assert r.call('ts_native_swap',1,4)==0
assert state==(bytes(u.mem_read(raw,30710)),bytes(u.mem_read(sounds,628)))
r.w32(root+16,raw-28)
if m.get('track_swap381'):
 r.w32(0x406fa02c,123)
 assert r.call('ts_native_swap',1,4)==0
 assert state==(bytes(u.mem_read(raw,30710)),bytes(u.mem_read(sounds,628)))
 r.w32(0x406fa02c,0)
 for field,value in ((root+16,0x41800000),(0x40a7887c,raw+30710),(0x468f6e80,1234),(0x406fa02c,123)):
  prior=r.r32(field)
  def race(u,pc,size,data):r.w32(field,value)
  hook=u.hook_add(UC_HOOK_CODE,race,begin=s['ts_exchange'],end=s['ts_exchange'])
  assert r.call('ts_native_swap',1,4)==0
  u.hook_del(hook);r.w32(field,prior)
  assert state==(bytes(u.mem_read(raw,30710)),bytes(u.mem_read(sounds,628)))
 print('PASS same-ID wrong-project refusal; owner/active/generation races rejected before writes; other95 patterns and kits unchanged')
r.w32(0x40a7883c,1);assert r.call('ts_native_swap',1,4)==0;r.w32(0x40a7883c,0)
print('PASS native getters resolve sequence/plock/sound/volume; stopped-only operation and notifications; double swap restores all native bytes')
delegated=[];bind(s['ts_old_key'],lambda a:delegated.append(a[0]) or 17);bind(s['ts_old_encoder'],lambda a:19);bind(al['sx_track'],lambda a:1);bind(al['ts_notice'],lambda a:0)
if 'ts_tree_edit' in al:bind(al['ts_tree_edit'],lambda a:0)
for k in ['gc_page','sx_submenu','du_page','mq_page']:r.w32(al[k],0)
r.w32(al['menu'],1);r.w32(al['gc_level'],2);r.w32(al['gc_tree_cursor'],3)
event=0x42031000
delta=[0];bind(0x4006f73a,lambda a:delta[0])
def turn(v):delta[0]=v;u.mem_write(event,struct.pack('>6I',0x400fbebc,0,1,1,v&0xffffffff,0));return r.call('ts_encoder',event)
r.w32(al['gc_tree_cursor'],0)
for sign in (1,-1):
 for i in range(20):
  prior=r.r32(al['gc_tree_cursor']);assert turn(sign*(1+i%4))==1
  assert r.r32(al['gc_tree_cursor'])==(prior+sign)%4
r.w32(al['gc_tree_cursor'],3)
def key(code,flags):u.mem_write(event,struct.pack('>6I',0x400fc20c,0,1,code,flags,0));return r.call('ts_key',event)
assert key(32,1)==1 and key(32,16)==1 and r.r32(s['ts_page'])==1 and r.r32(s['ts_source'])==1
assert key(10,1)==17 and delegated[-1]==event
assert key(12,1)==1 and key(12,16)==1 and r.r32(s['ts_page'])==0
render=[];bind(0x400423e4,lambda a:render.append(a[0]) or 0)
for fn,count in [('ts_track_menu',4),('ts_page_menu',3)]:
 r.call(fn,0,0x93010000);obj=render[-1];v=r.r32(obj);assert r.call(r.r32(v+12),obj)==count
 labels=[]
 for i in range(count):
  u.reg_write(C.UC_M68K_REG_A0,access);r.call(r.r32(v+16),obj,i);item=r.r32(access);labels.append(r.string(r.r32(item+12)))
 assert labels==(['SCRM','S.Chn','Human','Swap'] if count==4 else ['From','To','Swap']),labels
print('PASS native MenuView rows, DATA opens Swap, current-track default, BACK exit and transport delegation')
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(dict(native_swap=True,native_menu=True,stopped_only=True,level_bits=16,menu_turns=40,other_patterns_unchanged=95,other_kits_unchanged=95,context_races_rejected=4 if m.get('track_swap381') else 0,hardware_tested=False),indent=2))
