"""Preuves v55 : menus sans transition, modificateurs ordonnes, sauvegarde et clavier natif."""
import sys,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from boot_candidate import ROOT,boot
from test_seq_gen_menu import Rig,EVENT
from unicorn import UC_HOOK_CODE

def fixture(stem):
 m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'))
 sy={**m['beat_repeat_symbols'],**m['repeat_latch']['symbols'],**m['fx_menu']['symbols']};r=Rig(im,{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in sy.items()}});u=r.u;u.mem_map(0x46700000,len(mem[0][1]));u.mem_write(*mem[0]);u.mem_map(0xfc070000,4096);held=set();log=[];files={};state=dict(path='',pos=0,mode='',pending=b'');clock=[1000000]
 def bind(at,fn):
  if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 bind(sy['fx_query_original'],lambda a:int(a[0] in held));bind(sy['fx_show'],lambda a:log.append(('show',a[0])) or 0);bind(sy['fx_previous_draw'],lambda a:88);bind(sy['fx_notice'],lambda a:log.append(('notice',r.string(a[0]))) or 0)
 bind(0x40076bee,lambda a:0);bind(0x400d0a10,lambda a:1)
 def native(a):
  e=struct.unpack('>6I',u.mem_read(a[1],24));log.append(('native',e[3],r.r32(sy['fx_force_func']),r.r32(sy['fx_force_track'])));return 77
 bind(sy['fx_native_encoder'],native)
 kit,vt,get,data=0x93180000,0x93181000,0x93182000,0x93183000;r.w32(kit+48,vt);r.w32(vt+40,get);u.mem_write(get,b'\x20\x3c'+struct.pack('>I',data)+b'\x4e\x75');r.w32(data+4,0);bind(0x400cf866,lambda a:kit);bind(0x4001e318,lambda a:0)
 def op(a):state.update(path=r.string(a[0]),mode=r.string(a[1]),pos=0,pending=b'');return int(state['mode']=='r' and state['path'] not in files)
 def rd(a):
  raw=files.get(state['path'],b'')[state['pos']:state['pos']+a[1]];state['pos']+=len(raw)
  if raw:u.mem_write(a[0],raw)
  return len(raw)
 def wr(a):state['pending']+=bytes(u.mem_read(a[0],a[1]));return a[1]
 def close(a):
  if state['mode']=='w':files[state['path']]=state['pending']
  return 0
 for at,fn in [(0x4007bc5e,op),(0x4007baaa,rd),(0x4007bb0a,wr),(0x4007bc1c,close),(0x4007bb76,lambda a:0),(0x4007e2f6,lambda a:0)]:bind(at,fn)
 def key(code,flags=1,ms=0):
  clock[0]=(clock[0]+135168*ms)&0xffffffff;r.w32(0xfc07000c,clock[0]);held.add(code) if flags&1 else held.discard(code);u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,code,flags,0));return r.call('br_key_hook',EVENT),r.r32(EVENT+12)
 def turn(knob,delta=1):r.delta=delta;u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,knob,0,0));return r.call('fx_encoder_hook',0,EVENT)
 r.w32(0x40fe4178,0);r.w32(sy['br_history'],0x93190000);r.w32(sy['br_old_key'],0)
 return r,sy,held,log,files,key,turn,data,bind

def main():
 for stem in sys.argv[1:]:
  r,s,h,l,f,key,turn,data,bind=fixture(stem)
  lean=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())['fx_menu'].get('lean_fx',False)
  order_del=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())['fx_menu'].get('delay_selector_order',[2,1,0,3,4])
  cases=0
  order_rev=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())['fx_menu'].get('reverb_selector_order',[4,3,0,1,2,5,6])
  for knob,name,order in [(15,'cr_mode',order_del),(14,'ch_mode',order_rev)]:
   for mode in order:
    for sign in (-1,1):
     r.w32(s[name],mode);key(2);state=bytes(r.u.mem_read(s['cr_send'],24));ch=[bytes(r.u.mem_read(s[k],24)) for k in ('fx_aux_ch','fx_aux_vi')];turn(knob,999*sign);turn(knob,999*sign)
     assert r.r32(s[name])==mode,'audition changed effect before release';want=order[max(0,min(len(order)-1,order.index(mode)+sign))];assert r.r32(s['fx_menu_cursor'])==order.index(want)
     assert bytes(r.u.mem_read(s['cr_send'],24))==state and [bytes(r.u.mem_read(s[k],24)) for k in ('fx_aux_ch','fx_aux_vi')]==ch
     key(2,0);assert r.r32(s[name])==want and not r.r32(s['fx_menu_open']);cases+=1
   key(2);turn(knob);turn(knob);old=r.r32(s[name]);key(12);key(12,0);key(2,0);assert r.r32(s[name])==old and not r.r32(s['fx_menu_open'])
  print('PASS',cases,'menu positions: no sound mode change until physical TRACK release; BACK cancels',stem,flush=True)
  # Matrice complete des controles et delegations natives.
  h.clear();h.add(1)
  for cm,knob,mods,field in [(3,15,{1},0),(3,15,{1,2},1),(4,8,{1},2)]:
   if lean:continue
   r.w32(s['cr_mode'],cm);h.clear();h.update(mods);l.clear();turn(knob);assert l==[('show',field)],l
  for mode,knob,mods,field in [(1,14,set(),3),(2,14,{1},4),(3,14,set(),6),(3,14,{1},7),(3,14,{1,2},8),(4,14,{1},6),(4,14,{1,2},7),(4,9,{1},9),(4,9,{1,2},8),(5,14,{1},3),(6,14,{1,2},4),(5,9,{1},5)]:
   if lean and mode not in (1,2,3):continue
   r.w32(s['ch_mode'],mode);h.clear();h.update(mods);l.clear();turn(knob);assert l==[('show',field)],(mode,mods,l)
  for mode,knob,mods,want in [(4,15,set(),(15,0,0)),(4,8,{1,2},(15,1,0)),(0,15,{1},(15,1,0))]:
   if lean and mode!=0:continue
   r.w32(s['cr_mode'],mode);h.clear();h.update(mods);l.clear();turn(knob);assert l==[('native',*want)],l
  for mode in (4,5,6):
   if lean:continue
   r.w32(s['ch_mode'],mode);h.clear();l.clear();turn(14);assert l==[('native',14,0,0)],l
  for field,name in [(2,'cr_send'),(5,'fx_aux_ch'),(9,'fx_aux_vi')]:
   if lean:continue
   for lane in range(6):r.w32(data+4,lane);r.call('fx_parameter',field,127);assert r.r32(s[name]+4*lane)==127;r.call('fx_parameter',field,(-999)&0xffffffff);assert r.r32(s[name]+4*lane)==0
  h.clear();
  if 'last_input' in s:r.w32(0xfc07000c,r.r32(s['last_input'])+150000000)
  r.call('fx_service');saved=f['/FxMix.cfg'];assert len(saved)==60
  rr,ss,hh,ll,ff,*_=fixture(stem);ff['/FxMix.cfg']=saved;rr.call('fx_service');assert rr.r32(ss['ch_mode'])==r.r32(s['ch_mode'])
  print('PASS all solo/combined modifier mappings, native forwarding, six independent tracks, settings save/load',stem,flush=True)
  # FUNC d'abord : maintien consomme, tap stock differe. TRACK d'abord reste transmis.
  r,s,h,l,f,key,turn,data,bind=fixture(stem);key(1);assert key(2)==(0,0);r.w32(s['ch_mode'],1 if lean else 5);turn(14);depth=r.r32(s['fx_depth']);assert depth==65;assert key(2,0,500)==(0,0);assert not r.r32(s['fx_tap_force']);key(1,0)
  key(1);assert key(2)==(0,0);assert key(2,0,50)==(2,2);assert r.r32(s['fx_tap_force'])==1;r.call('fx_draw',0,0);assert not r.r32(s['fx_tap_force']);key(1,0)
  assert key(2)==(2,2);assert key(1)==(1,1);key(1,0);key(2,0)
  # Vrai verrou retrig puis raccourcis stock sans sortir du verrou.
  key(2);key(4);key(4,0,80);key(4,1,100);assert r.r32(s['bl_latched']);key(4,0);key(2,0);key(1)
  for code in (5,13):
   for flags in (3,34,2):assert key(code,flags)==(code,code);assert r.r32(s['bl_latched']) and r.r32(s['br_keys'])==3
  key(1,0);key(12);key(12,0);assert not r.r32(s['bl_latched'])
  print('PASS real key chain: FUNC-first hold/tap, reverse TRACK-first pass, retrig latch temp shortcut propagation',stem,flush=True)
  # Diagnostic : meme chainage reel, vraie duree physique et verrou synthetique.
  for enabled in (0,1):
   for release in (2,4):
    rr,ss,hh,ll,ff,kk,tt,dd,bb=fixture(stem);rr.w32(ss['dx_enabled'],enabled);notes=[]
    bb(ss['fx_notice'],lambda a:notes.append(rr.string(a[0])) or 0)
    kk(2);kk(4);kk(release,0,400);assert len([n for n in notes if n.startswith('A')])==(0 if 'dx_func_stage' in ss else enabled),notes
   rr,ss,hh,ll,ff,kk,tt,dd,bb=fixture(stem);rr.w32(ss['dx_enabled'],enabled);notes=[];bb(ss['fx_notice'],lambda a:notes.append(rr.string(a[0])) or 0)
   kk(2);kk(4);kk(4,0,80);kk(4,1,100);assert rr.r32(ss['bl_latched']);kk(4,0,500);kk(2,0);kk(12);assert not rr.r32(ss['bl_latched']);assert not [n for n in notes if n.startswith('A')],notes
  print('PASS diagnostics on/off: legacy gesture follows build policy; latch entry, release and BACK never show CPU popup',stem,flush=True)
  # Le vrai query detour force seulement les deux modificateurs.
  h.clear();r.w32(s['fx_force_active'],1);r.w32(s['fx_force_func'],1);r.w32(s['fx_force_track'],0);assert r.call(0x4007faf4,1)==1 and r.call(0x4007faf4,2)==0;r.w32(s['fx_force_active'],0)
  # Machine : delta accelere borne a un, Wizard impossible a sauter.
  for delta in (99,-99):
   r.w32(0xfc07000c,1000000);r.w32(s['machine_valid'],0);cur=0 if delta>0 else 17;seen=[cur]
   for i in range(len(json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())['tiny_extra']['menu_order'])-1):
    cur=r.call('fx_machine_step',cur,delta&0xffffffff);seen.append(cur);assert r.call('fx_machine_step',cur,delta&0xffffffff)==cur;r.w32(0xfc07000c,1000000+(i+1)*6000000)
   assert len(set(seen))==len(json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())['tiny_extra']['menu_order']) and 6 in seen and seen[-1]==(17 if delta>0 else 0),seen
  print('PASS modifier query and throttled machine selection visits every ID including Wizard',stem,flush=True)
if __name__=='__main__':main()
