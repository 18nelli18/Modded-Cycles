"""Preuve native USB et preferences, avec fichier modele pour les E/S disque."""
import sys,json,struct
from boot_candidate import ROOT,boot
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
for stem in (sys.argv[1:] or ['all-features-dx-toggle-test-v14','no-filter-dx-toggle-test-v14']):
 p=ROOT/'output/firmware'/(stem+'.syx');m=json.loads(p.with_suffix('.json').read_text());sy=m['symbols'];ps=m['persist_symbols'];im,mem=boot(p)
 def rig(saved=None):
  r=Rig(im,{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in {**sy,**ps}.items()}});u=r.u;u.mem_map(0x46700000,0x200000)
  for at,raw in mem:u.mem_write(at,raw)
  r.w32(0x40fe4178,0);r.w32(0x40a7883c,0);r.w32(0x404a09c8,5)
  log=[];files={'data':saved,'pos':0,'mode':'','pending':b''}
  def bind(at,fn):
   if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
   r.stubs[at]=fn
  bind(0x40004d9a,lambda a:0);bind(0x40004db4,lambda a:0)
  bind(sy['wf_usb_push'],lambda a:0)
  # CPUS cache control n'est pas implemente par Unicorn ; la copie native reste executee.
  raw=bytes(u.mem_read(sy['wf_usb_atomic'],80));i=raw.index(bytes.fromhex('4e7b0002'));at=sy['wf_usb_atomic']+i
  u.hook_add(UC_HOOK_CODE,lambda u,pc,size,d:u.reg_write(C.UC_M68K_REG_PC,pc+4),begin=at,end=at)
  u.hook_add(UC_HOOK_CODE,lambda u,pc,size,d:log.append(('mode',r.r32(u.reg_read(C.UC_M68K_REG_A7)+4))),begin=0x40004e04,end=0x40004e04)
  bind(0x400d0a10,lambda a:1)
  def cstr(at):return bytes(u.mem_read(at,64)).split(b'\0')[0].decode()
  def op(a):
   assert cstr(a[0])=='/ModSetup.cfg';files.update(mode=cstr(a[1]),pos=0,pending=b'');log.append(('open',files['mode']));return int(files['mode']=='r' and files['data'] is None)
  def rd(a):
   data=files['data'] or b'';chunk=data[files['pos']:files['pos']+a[1]];files['pos']+=len(chunk)
   if chunk:u.mem_write(a[0],chunk)
   return len(chunk)
  def wr(a):files['pending']+=bytes(u.mem_read(a[0],a[1]));return a[1]
  def close(a):
   if files['mode']=='w':files['data']=files['pending']
   return 0
  bind(0x4007bc5e,op);bind(0x4007baaa,rd);bind(0x4007bb0a,wr);bind(0x4007bb76,lambda a:0);bind(0x4007e2f6,lambda a:0);bind(0x4007bc1c,close)
  return r,files,log,bind
 def check(r,six):
  u=r.u
  for i in range(15):
   at,n,p2,p6=struct.unpack('>4I',u.mem_read(sy['wf_usb_patches']+i*16,16));assert bytes(u.mem_read(at,n))==bytes(u.mem_read(p6 if six else p2,n)),hex(at)
  assert r.r32(sy['wf_usb_six'])==six
 r,f,log,bind=rig();check(r,0)
 for v in (1,0,1,0):assert r.call('wf_usb_set',v)==1;check(r,v)
 assert [x[1] for x in log if x[0]=='mode']==[2,5]*4
 r.w32(0x40a7883c,1);assert r.call('wf_usb_set',1)==0;check(r,0)
 print('PASS',stem,'15 actual USB ranges, native detach/reattach on both transitions, playback guard',flush=True)
 def cfg(v):return bytes([77,83,48,49,v,v^255,165,90])
 for v in range(64):
  r,f,log,bind=rig(cfg(v));r.call('ms_draw',0,0);assert r.r32(sy['wf_stock'])==(v&1);assert r.r32(sy['lm_enabled'])==bool(v&8);assert r.r32(sy['dl_enabled'])==bool(v&16);assert r.u.mem_read(0x4018fddf,1)[0]==(not bool(v&4));assert r.r32(m['dx_symbols']['dx_enabled'])==bool(v&32);check(r,int(bool(v&2)))
  count=len(log);r.call('ms_draw',0,0);assert len(log)==count,'No repeated disk reads'
 for bad in (None,b'',cfg(64),cfg(31)[:-1],b'badcfg!!',cfg(31)+b'x',cfg(31)[:5]+b'\0'+cfg(31)[6:]):
  r,f,log,bind=rig(bad);r.call('ms_draw',0,0);check(r,0);assert r.r32(sy['wf_stock'])==1 and r.r32(sy['lm_enabled'])==0 and r.r32(sy['dl_enabled'])==0
 print('PASS all 64 preference combinations restored, missing/truncated/invalid files retain defaults, one startup read',flush=True)
 r,f,log,bind=rig();u=r.u;r.call('ms_draw',0,0)
 def key(code,flags):u.mem_write(0x93010000,struct.pack('>6I',0,0,0,code,flags,0));return r.call('ms_key',0x93010000)
 key(13,1);key(2,1);key(2,33);key(2,0);key(13,0)
 # Toutes les preferences sont sauvees ensemble a la fermeture.
 r.call(m['dx_symbols']['dx_set'],1);r.w32(sy['wf_stock'],0);r.w32(sy['lm_enabled'],1);r.w32(sy['dl_enabled'],1);u.mem_write(0x4018fddf,b'\0');assert r.call('wf_usb_set',1)==1
 key(12,1);r.w32(0x40a7883c,1);before=len(log);r.call('ms_draw',0,0);assert len(log)==before
 r.w32(0x40a7883c,0);r.call('ms_draw',0,0);assert f['data']==cfg(62),(f['data'],cfg(62))
 saved=f['data'];r,f,log,bind=rig(saved);r.call('ms_draw',0,0);check(r,1);assert r.r32(sy['lm_enabled'])==1 and r.r32(sy['dl_enabled'])==1
 assert r.r32(0x467b0000)!=0xffffffff
 print('PASS close menu saves all six preferences, playback defers disk writes, fresh native image reloads saved USB mode and toggles',flush=True)
