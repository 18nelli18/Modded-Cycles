"""188 : preuves natives exactes et cout en instructions, pas de CPU physique."""
"""Audit enregistrement repeat : vrai v25 contre raccourcis OFF/arme.
Aucun fichier firmware servi n'est modifie ; preuve samples/historique/etats.
"""
import json,os,pathlib,random,struct,subprocess,sys
from types import SimpleNamespace
from unicorn import m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from boot_candidate import ROOT
from test_governor_recovery import load,call
from test_seq_gen_menu import STACK,STOP
CANDIDATE=next((a for a in sys.argv[1:] if not a.startswith('--')),None)
BASELINE='staging/all-features-polivoks-cpu-trim-test-v154'
if CANDIDATE and not json.loads((ROOT/'output/firmware'/(CANDIDATE+'.json')).read_text())['shared_filter_enabled']:BASELINE='no-filter-wizard-polivoks-cpu-trim-test-v24'
ORIGIN=0x467ca000;RANGE='--range' in sys.argv;UNROLL=next((int(a.split('=')[1]) for a in sys.argv if a.startswith('--unroll=')),0)

def build():
 out=ROOT/('output/firmware/repeat-record-'+('range' if RANGE else 'audit')+('-u'+str(UNROLL) if UNROLL else ''));out.mkdir(exist_ok=True)
 cross=str(ROOT.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(pathlib.Path(cross).parent)+os.pathsep+os.environ['PATH']
 meta=json.loads((ROOT/'output/firmware/all-features-polivoks-cpu-trim-test-v25.json').read_text());sy=meta['beat_repeat_symbols']
 names=['br_valid','br_start','br_length','br_excluded','br_lane_wet','br_side','br_side_on','br_history','br_active','br_wet','br_keys']
 aliases={k:sy[k] for k in names};aliases.update(rr_native_render=0x467ab9fe,rr_native_mode=0x467ab734)
 (out/'module.ld').write_text(f'SECTIONS {{ .text {ORIGIN:#x} : {{ *(.text*) *(.rodata*) }} }}'+''.join(f'\nPROVIDE({k} = {v:#x});' for k,v in aliases.items()))
 flags=['-DRR_LOCAL_PLAIN=1','-DRR_FAST_RECORD=1']+(['-DRR_RECORD_RANGE=1'] if RANGE else [])+(['-DRR_RECORD_UNROLL='+str(UNROLL)] if UNROLL else [])
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror',*flags,'-c',str(ROOT/'tools/machines/cpu_audit/repeat_fades.c'),'-o',str(out/'module.o')],check=True)
 subprocess.run([cross+'ld.exe','-T',str(out/'module.ld'),'-o',str(out/'module.elf'),str(out/'module.o')],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary',str(out/'module.elf'),str(out/'module.bin')],check=True)
 syms={x[2]:int(x[0],16) for line in subprocess.check_output([cross+'nm.exe','--defined-only',str(out/'module.elf')],text=True).splitlines() if len(x:=line.split())==3}
 return out,syms['rr_render']

def equal(rigs,label):
 for base,size in [(0x41000000,12*131072*2),(0x80001858,768),(0x80010000,768)]:assert bytes(rigs[0].u.mem_read(base,size))==bytes(rigs[1].u.mem_read(base,size)),(label,hex(base))
 lo=rigs[0].s['br_old_track_leds'];end=rigs[0].s['br_end'];assert rigs[0].u.mem_read(lo,end-lo)==rigs[1].u.mem_read(lo,end-lo),(label,'repeat state')

def main():
 out,target=(ROOT/('output/firmware/repeat-record-rebuild-'+CANDIDATE.rsplit('-',1)[-1]),None) if CANDIDATE else build();out.mkdir(exist_ok=True);a=SimpleNamespace(steady=False);rng=random.Random(136);totals=[0,0];modes={}
 for stereo in (False,True):
  rigs=[];traces=[[],[]]
  for index in range(2):
   r,meta=load(CANDIDATE if index and CANDIDATE else BASELINE);r.s=meta['beat_repeat_symbols']
   if index and not CANDIDATE:
    at=meta['recovery_symbols']['rr_render'];assert bytes(r.u.mem_read(at,8)).hex()=='4fefffd848d73cfc'
    r.u.mem_write(ORIGIN,(out/'module.bin').read_bytes());r.u.mem_write(at,b'\x4e\xf9'+struct.pack('>I',target)+b'\x4e\x71')
   for name,value in [('br_history',0x41000000),('br_keys',3),('br_requested',-1),('br_blocks',4094),('br_side',0x80010000 if stereo else 0),('br_side_on',0x80011000 if stereo else 0)]:r.w32(r.s[name],value&0xffffffff)
   r.w32(0x40a7883c,1);r.w32(0x40a78840,1);r.w32(0x40149310,57600);r.w32(r.s['br_mask_address'],0x80012000);rigs.append(r)
  bounds=[-2147483648,2147483647,0]+[q*32768+d for q in (-32768,-32767,-1,0,1,32767,32768) for d in (-1,0,1)]
  for mode in ('off','armed','leftover','stopped','off-valid','armed-valid','wet-tail'):
   costs=[[],[]]
   for case in range(32):
    data=[rng.choice(bounds) if case%2 else rng.randrange(-0x20000000,0x20000000) for _ in range(384)]
    for j,r in enumerate(rigs):
     for key,v in [('br_keys',0 if mode.startswith('off') else 3),('br_requested',-1),('br_wet',32768 if mode=='wet-tail' else 0),('br_valid',int(mode.endswith('valid'))),('br_active',case%16),('br_cancel',0),('br_blocks',4095+case)]:r.w32(r.s[key],v&0xffffffff)
     r.w32(0x40a7883c,0 if mode=='stopped' else 1);r.u.mem_write(r.s['br_lane_wet'],struct.pack('>6I',*([0]*6 if mode!='leftover' else [0,1024,32768,65536,0,16384])))
     r.u.mem_write(0x80012000,bytes([case%64]))
     for lane in range(6):r.w32(0x80011000+4*lane,int(case%4==0 or (case%4!=1 and (lane+case)%3!=0)))
     for track in range(12):r.u.mem_write((0x80001858 if track<6 else 0x80010000)+128*(track%6),struct.pack('>32i',*data[32*track:32*(track+1)]))
     r.count=0;call(r,r.s['br_audio']);costs[j].append(r.count)
    equal(rigs,(stereo,mode,case))
   modes[str(stereo)+'-'+mode]={'totals':[sum(v) for v in costs],'peak':[max(v) for v in costs]};print('PASS',stereo,mode,modes[str(stereo)+'-'+mode],flush=True)
  for r in rigs:
   for key,v in [('br_keys',3),('br_requested',-1),('br_wet',0),('br_valid',0),('br_active',-1),('br_cancel',0),('br_blocks',4094)]:r.w32(r.s[key],v&0xffffffff)
   r.u.mem_write(r.s['br_lane_wet'],bytes(24));r.w32(0x40a7883c,1)
  for block in range(256 if a.steady else 96):
   samples=[rng.choice([-2147483648,2147483647,rng.randint(-2147483648,2147483647),0]) for _ in range(12*32)]
   for index,r in enumerate(rigs):
    r.w32(r.s['br_keys'],3 if a.steady else (0 if block>=32 and block%24 in (21,22,23) else 3))
    r.w32(r.s['br_requested'],0 if a.steady or block<32 else ((block-32)//4)%16)
    r.u.mem_write(0x80012000,bytes([0 if a.steady or block<32 else (block//3)%64]))
    for track in range(12):
     base=0x80001858 if track<6 else 0x80010000
     r.u.mem_write(base+(track%6)*128,struct.pack('>32i',*samples[track*32:(track+1)*32]))
    for lane in range(6):r.w32(0x80011000+lane*4,int((lane+block)%3!=0))
    r.u.mem_write(STACK,struct.pack('>I',STOP));r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
    r.count=0;r.u.emu_start(r.s['br_audio'],STOP,count=1000000)
    assert r.u.reg_read(mk.UC_M68K_REG_PC)==STOP
    assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
    totals[index]+=r.count;traces[index].append(r.count)
   for base,length in [(0x41000000,12*131072*2),(0x80001858,6*128),(0x80010000,6*128)]:
    assert bytes(rigs[0].u.mem_read(base,length))==bytes(rigs[1].u.mem_read(base,length)),(stereo,block,hex(base))
   for name in ('br_wet','br_valid','br_active','br_blocks','br_start','br_length'):
    assert rigs[0].r32(rigs[0].s[name])==rigs[1].r32(rigs[1].s[name]),name
   assert bytes(rigs[0].u.mem_read(rigs[0].s['br_lane_wet'],24))==bytes(rigs[1].u.mem_read(rigs[1].s['br_lane_wet'],24))
  # Frontieres du chemin plateau, phases courtes et wrap 32 bits.
  for length in (1,16,31,32,33,63,127,375,4096,126976):
   for elapsed in (0,1,31,32,length-1,length,length+32,131040,131071,131072,0xfffffff0):
    elapsed&=0xffffffff;mask=rng.randrange(64);blocks=rng.choice((0,4095,4096,0x7ffffff,0xfffffff));now=(blocks<<5)&0xffffffff
    samples=[rng.choice((-2147483648,2147483647,rng.randint(-2147483648,2147483647),0)) for _ in range(384)]
    for r in rigs:
     for name,value in [('br_keys',3),('br_requested',0),('br_active',0),('br_cancel',0),('br_valid',1),('br_length',length),('br_start',(now-elapsed)&0xffffffff),('br_wet',65536),('br_blocks',blocks)]:r.w32(r.s[name],value)
     r.u.mem_write(0x80012000,bytes([mask]))
     for lane in range(6):r.w32(r.s['br_lane_wet']+4*lane,0 if mask&(1<<lane) else 65536)
     for track in range(12):
      base=0x80001858 if track<6 else 0x80010000
      r.u.mem_write(base+128*(track%6),struct.pack('>32i',*samples[32*track:32*(track+1)]))
     r.u.mem_write(STACK,struct.pack('>I',STOP));r.u.reg_write(mk.UC_M68K_REG_A7,STACK);r.u.emu_start(r.s['br_audio'],STOP,count=1000000)
     assert r.u.reg_read(mk.UC_M68K_REG_PC)==STOP
    for base,size in [(0x41000000,12*131072*2),(0x80001858,768),(0x80010000,768)]:
     assert bytes(rigs[0].u.mem_read(base,size))==bytes(rigs[1].u.mem_read(base,size)),('frontiere',stereo,length,elapsed,hex(base))
  print('REPEAT first8 old/new',traces[0][:8],traces[1][:8],'peak',max(traces[0]),max(traces[1]),flush=True)
  print('PASS repeat actif et 110 frontieres : audio/historique/etats identiques, stereo',stereo,flush=True)
 print('PASS repeat actif totals old/new',totals,'; aucune extrapolation CPU physique',flush=True)
 (out/'result.json').write_text(json.dumps({'active_instructions':totals,'modes':modes,'candidate':CANDIDATE,'range':RANGE,'unroll':UNROLL,'hardware_tested':False,'served':False},indent=2))
if __name__=='__main__':main()
