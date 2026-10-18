"""Vrais boots signes, init/chargement projet et cache pour toutes les familles."""
import argparse,hashlib,json,pathlib,struct,sys,time
from unicorn import m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,STACK,STOP
import build,test_sdvintage_7th as T
ROOT=HERE.parent.parent

def check(prefix):
 meta=json.loads(prefix.with_suffix('.json').read_text());case=meta['case'];img,memories,ts=boot_case(prefix);r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in memories:u.mem_write(at,raw)
 hooks={}
 for site in (0x4005b4a8,0x40061564):
  raw=bytes(u.mem_read(site,8))
  if raw[:2]==bytes.fromhex('4ef9'):
   target=int.from_bytes(raw[2:6],'big');hooks[target]=bytes(u.mem_read(target,48));assert any(hooks[target]),(prefix,hex(target),'code absent')
 def project():
  src=0x930b0000;dst=0x930b1000;u.mem_write(src,bytes(128));u.mem_write(dst,bytes(128));u.mem_write(src+28,b'\x5a');u.reg_write(mk.UC_M68K_REG_A2,dst);u.reg_write(mk.UC_M68K_REG_A3,src);u.reg_write(mk.UC_M68K_REG_A7,STACK);u.reg_write(mk.UC_M68K_REG_SR,0x2700)
  u.emu_start(0x4005b4a8,0x4005b4b0,count=500000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4005b4b0,(prefix,'load stalled');assert bytes(u.mem_read(dst+28,1))==b'\x5a';assert u.reg_read(mk.UC_M68K_REG_A7)==STACK
  u.reg_write(mk.UC_M68K_REG_A0,dst);u.reg_write(mk.UC_M68K_REG_D0,0);u.reg_write(mk.UC_M68K_REG_A7,STACK)
  u.emu_start(0x40061564,0x4006156c,count=500000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4006156c,(prefix,'init stalled');assert bytes(u.mem_read(dst+27,1))==b'\0';assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-4;assert int.from_bytes(u.mem_read(STACK-4,4),'big')==16
 project();r.call(0x4007929c)
 for at,raw in hooks.items():assert bytes(u.mem_read(at,len(raw)))==raw,(prefix,hex(at),'cache ecrase hook')
 project();r.call(0x4005a274)
 count=6+(bool(case['wizard']) if case['mask'] else 0)+case['mask'].bit_count();assert r.r32(T.ROW_COUNT)==count,(prefix,r.r32(T.ROW_COUNT),count)
 return dict(sourceSha=meta['sourceSha'],fixtureSha=hashlib.sha256(prefix.with_suffix('.syx').read_bytes()).hexdigest(),case=case,hooks=[hex(at) for at in hooks],passed=['signed image boot','project load hook','project init hook','disk cache preservation','project hooks after cache','native machine table constructor'])

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--watch',action='store_true');p.add_argument('--expected',type=int,default=48);p.add_argument('--resume',action='store_true');a=p.parse_args();folder=ROOT/'build/startup-matrix';out=ROOT/'build/startup-matrix-proof';out.mkdir(exist_ok=True);done=set();start=time.monotonic()
 h=hashlib.sha256();web=ROOT/'docs/flasher-machine-combinations-test'
 for f in sorted(web.iterdir(),key=lambda f:f.name):
  if f.suffix=='.js' or f.name=='index.html':h.update((f.name+'\0').encode());h.update(f.read_bytes())
 current=h.hexdigest()
 while True:
  for file in sorted(folder.glob('*.json')):
   if file.stem in done:continue
   if json.loads(file.read_text()).get('sourceSha')!=current:continue
   target=out/file.name
   if a.resume and target.exists():
    prior=json.loads(target.read_text());meta=json.loads(file.read_text())
    if prior.get('sourceSha')==meta['sourceSha'] and prior.get('fixtureSha')==hashlib.sha256(file.with_suffix('.syx').read_bytes()).hexdigest():done.add(file.stem);continue
   result=check(file.with_suffix(''));target.write_text(json.dumps(result,indent=2),encoding='utf-8');done.add(file.stem);print('PASS BOOT/PROJECT/CACHE',file.stem,len(done),'/',a.expected,flush=True)
  if len(done)>=a.expected:break
  if not a.watch:raise AssertionError(('missing signed cases',len(done),a.expected))
  if time.monotonic()-start>1800:raise TimeoutError('build matrix incomplete')
  time.sleep(2)
 print('PASS ALL STARTUP FAMILIES',len(done),'real signed boots and project hooks',flush=True)
if __name__=='__main__':main()
