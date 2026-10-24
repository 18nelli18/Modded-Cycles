"""Vrai binaire compose : navigation, stockage sixpistes, live/locks natifs et bornes."""
import sys,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from boot_candidate import ROOT,boot
from test_seq_gen_menu import Rig,STACK,EVENT
from unicorn import UC_HOOK_CODE,m68k_const as C

def fixture(stem,saved=None):
 m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));meta=m['scramble_mask'];sy={**m['symbols'],**meta['symbols']};r=Rig(im,{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in sy.items()}});u=r.u;u.mem_map(0x46700000,max(0x100000,(len(mem[0][1])+4095)&~4095));u.mem_map(0x80000000,0x20000)
 for at,raw in mem:u.mem_write(at,raw)
 r.w32(0x40fe4178,0);r.w32(0x40a7883c,0);state={'lane':0,'data':saved,'pos':0,'mode':'','pending':b'','opens':[]};r.meta=meta;r.state=state;r.m=m
 def bind(at,fn):
  if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 r.bind=bind;bind(0x40012412,lambda a:state['lane']);bind(0x400d0a10,lambda a:1);bind(meta['symbols']['sx_root_draw'],lambda a:0);bind(meta['symbols']['sx_sub_draw'],lambda a:0)
 def op(a):
  assert r.string(a[0])=='/Scramble.cfg';state.update(mode=r.string(a[1]),pos=0,pending=b'');state['opens'].append(state['mode']);return int(state['mode']=='r' and state['data'] is None)
 def rd(a):
  data=state['data'] or b'';s=data[state['pos']:state['pos']+a[1]];state['pos']+=len(s)
  if s:u.mem_write(a[0],s)
  return len(s)
 def wr(a):state['pending']+=bytes(u.mem_read(a[0],a[1]));return a[1]
 def close(a):
  if state['mode']=='w':state['data']=state['pending']
  return 0
 for at,fn in [(0x4007bc5e,op),(0x4007baaa,rd),(0x4007bb0a,wr),(0x4007bc1c,close),(0x4007bb76,lambda a:0),(0x4007e2f6,lambda a:0)]:bind(at,fn)
 return r

def key(r,code,flags):r.u.mem_write(EVENT,struct.pack('>6I',0,0,123,code,flags,0));return r.call('sx_key',EVENT)
def encoder(r,d):r.delta=d;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,1,0,0));return r.call('sx_encoder',EVENT)
def click(r):key(r,32,1);key(r,32,16)
def main():
 reports=[]
 for stem in (sys.argv[1:] or ['all-features-polivoks-cpu-trim-test-v46','no-filter-wizard-polivoks-cpu-trim-test-v46nf']):
  r=fixture(stem);r.call(0x4005a274);r.call('sx_draw',0,0);assert [r.call('sx_mask',i) for i in range(6)]==[60]*6
  r.w32(r.s['menu'],1);r.w32(r.s['row'],6);click(r);assert r.r32(r.s['sx_submenu'])==1 and r.r32(r.s['menu'])==1
  # Six pistes distinctes, six cases ; pas de bascule a la release dupliquee.
  for lane in range(6):
   r.state['lane']=lane;r.w32(r.s['sx_subrow'],lane);before=r.call('sx_mask',lane);click(r);key(r,32,16);assert r.call('sx_mask',lane)==before^(1<<lane)
   for other in range(6):assert r.call('sx_mask',other)==60^(1<<other) if other<=lane else r.call('sx_mask',other)==60
  encoder(r,1);assert r.r32(r.s['sx_subrow'])==0;encoder(r,-1);assert r.r32(r.s['sx_subrow'])==5
  key(r,12,1);assert not r.r32(r.s['sx_submenu']) and r.r32(r.s['menu'])==1 and r.r32(r.s['row'])==6;key(r,12,16)
  r.w32(0x40a7883c,1);old=len(r.state['opens']);r.call('sx_draw',0,0);assert len(r.state['opens'])==old
  r.w32(0x40a7883c,0);r.call('sx_draw',0,0);saved=r.state['data'];assert saved and len(saved)==18
  key(r,12,1);key(r,12,16);assert not r.r32(r.s['menu'])
  q=fixture(stem,saved);q.call('sx_draw',0,0);assert [q.call('sx_mask',i) for i in range(6)]==[60^(1<<i) for i in range(6)]
  for bad in (b'',saved[:-1],saved+b'x',b'X'+saved[1:],saved[:4]+bytes([64])+saved[5:]):
   q=fixture(stem,bad);q.call('sx_draw',0,0);assert [q.call('sx_mask',i) for i in range(6)]==[60]*6
  print('PASS',stem,'DATA/BACK,7lignes racine,6cases,6masques independants,sauvegarde/reload et fichiers invalides',flush=True)
  # Getter/setter natifs : bornes et CC reels, notification appliquee au son.
  from test_scramble import KIT,SVT,SRAW,SGET,NOTIFY,CTX,ZVT,ZERO
  r=fixture(stem);r.call(0x4005a274);lane=3;r.state['lane']=lane;handle=KIT+212+68*lane
  r.bind(0x400cf866,lambda a:KIT);r.bind(0x4000f26c,lambda a:CTX);r.bind(ZERO,lambda a:0);r.bind(NOTIFY,lambda a:0);r.bind(0x400802ec,lambda a:0);r.bind(r.meta['aliases']['sx_notice'],lambda a:0)
  r.w32(handle,SVT);r.w32(SVT+40,SGET);r.w32(SVT+16,NOTIFY);r.u.mem_write(SGET,b'\x20\x3c'+struct.pack('>I',SRAW)+b'\x4e\x75');r.w32(CTX,0x400fd134);r.w32(CTX+4,handle);r.w32(KIT+116+8*(63+lane),ZVT);r.w32(KIT+116+620,ZVT);r.w32(ZVT+80,ZERO)
  slotlist=r.meta['slots'];live_cases=0;step_cases=0
  for machine in [i for i in range(r.m['tiny_extra']['machine_count']) if i!=17]:
   for mask in [0,1,2,4,8,16,32,60,63]:
    before=bytearray([0xa5]*100)
    for sl in range(33):struct.pack_into('>H',before,20+2*sl,64*256)
    before[38]=machine;r.u.mem_write(SRAW,bytes(before));r.u.mem_write(r.s['sx_masks']+lane,bytes([mask]));r.call('sx_run');after=bytes(r.u.mem_read(SRAW,100))
    selected=[sl for i,sl in enumerate(slotlist) if mask&(1<<i) and (machine!=6 or i<2)];allowed={20+2*sl+j for sl in selected for j in (0,1)};assert all(after[i]==before[i] for i in range(100) if i not in allowed),(machine,mask,'outside live');live_cases+=1
    for sl in selected:
     d=r.call(0x4005a692,sl,machine);bnd=0x931a0000;r.u.reg_write(C.UC_M68K_REG_A0,bnd);r.call(0x4005a65a,d);lo,hi=struct.unpack('>ii',r.u.mem_read(bnd,8));value=struct.unpack_from('>H',after,20+2*sl)[0];assert lo<=value<=hi,(machine,mask,sl,lo,value,hi)
    # Meme masque par piste dans les locks, pas le masque de la piste selectionnee UI.
    event,locks=0x93180000,0x93181000;r.u.mem_write(event,bytes(76));r.u.mem_write(locks,bytes(300));r.w32(event+8,lane);r.w32(event+40,577);r.w32(event+44,SRAW);r.w32(event+72,locks);r.call('sx_step',event)
    count=r.r32(locks+8);ids=[struct.unpack('>H',r.u.mem_read(locks+20+8*i,2))[0] for i in range(count)];assert ids==selected,(machine,mask,ids,selected);assert bytes(r.u.mem_read(SRAW,100))==after;assert r.r32(event+40)==513;step_cases+=1
  # Un pool plein est laisse intact si les nouveaux champs ne tiennent pas.
  r.u.mem_write(r.s['sx_masks']+lane,b'\x3f');r.w32(event+40,577);r.w32(locks+8,33)
  for i in range(33):r.u.mem_write(locks+20+8*i,struct.pack('>HHI',100+i,1234,0))
  prior=bytes(r.u.mem_read(locks,300));r.call('sx_step',event);assert bytes(r.u.mem_read(locks,300))==prior
  reports.append(dict(candidate=stem,sha256=r.m['sha256'],native_live_cases=live_cases,native_step_cases=step_cases,per_track_persistence=True,invalid_files_rejected=True,full_pool_atomic=True));print('PASS',live_cases,'SCRAMBLE natifs et',step_cases,'evenements de locks, machines audio,6slots,autres octets intacts',flush=True)
 (ROOT/('output/firmware/scramble-mask-proof-'+(reports[0]['candidate'].rsplit('-',1)[-1].replace('nf',''))+'.json')).write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
