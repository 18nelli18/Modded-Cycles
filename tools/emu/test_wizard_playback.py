"""Lecture PCM complete Wizard v20/v21 : filtres OFF/ON, mono/stereo et retrigs.
Les autres voix ne doivent pas changer. Tables SRAM natives restaurees (note137) :
les sixvoix du mix peuvent etre audibles. Aucun resultat CPU physique deduit.
"""
import json,math,pathlib,struct,sys,subprocess
import numpy as np
from unicorn import UC_HOOK_CODE,m68k_const as C
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from boot_candidate import ROOT,boot,load
from chord_boot_fixture import boot_chord_waves
import mcengine as E
from test_model_tg import engine
import emac
from emac_state import ExtendedEMAC
emac.EMAC=ExtendedEMAC
original=subprocess.run
def cross(cmd,*args,**kw):
 if isinstance(cmd,list) and cmd[0]=='m68k-linux-gnu-objdump':cmd=[str(ROOT.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe'),*cmd[1:]]
 return original(cmd,*args,**kw)
subprocess.run=cross

def fixtures(stereo,cutoff,resonance,stems=None,native_chordkeys=False,runtime_transform=None,audit_count=True):
 profile=json.loads((ROOT/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());sy={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()};engines=[]
 for stem in (stems or ['all-features-polivoks-cpu-test-v20',sys.argv[1] if len(sys.argv)>1 else 'all-features-polivoks-cpu-test-v21']):
  im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));rt=boot_chord_waves(load(ROOT/'firmware/model-cycles_OS1.13.syx'),mem[0][0],mem[0][1])
  if runtime_transform:rt=runtime_transform(rt)
  e=engine(im,payload=(mem[0][0],rt));m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())
  # L'image cachee par boot() est APRES clearBSS : les sources des tables SRAM
  # sont deja effacees. Le vrai demarrage les copie AVANT ce clear. Rejouer
  # ici les deux copies depuis le MAIN candidat brut, puis ses banques Syntakt.
  initial=load(ROOT/'output/firmware'/(stem+'.syx'))
  for lo,hi,dst in ((0x4019b590,0x401a2a50,0x80000000),(0x401a2a50,0x401aa140,0x80008000)):
   e.uc.mem_write(dst,initial[lo-0x40000400:hi-0x40000400])
  for off,at,size in [(0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)]:e.uc.mem_write(at,rt[off:off+size])
  if m.get('polivoks_inspired'):
   raw=ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-test-',1)[-1]+'/module.bin');e.emac.install(emac.disasm(str(raw),0x467c7000,0x467c7000,0x467c7000+raw.stat().st_size))
  if m.get('feral_replaces_tiny'):
   fr=m['feral'];path=ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-test-',1)[-1]+'/feral-code.bin');e.emac.install(emac.disasm(str(path),fr['code'],fr['code'],fr['code']+fr['code_bytes']))
  if m.get('mixer_headroom'):
   # Nouvelles copies natives hors des plages historiques de mcengine.
   for row in m['mixer_headroom']['kernels']:
    path=ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-test-',1)[-1]+'/mixer147-'+str(row['gains'])+'.bin')
    assert bytes(e.uc.mem_read(row['code'],row['size']))==path.read_bytes()
    e.emac.install(emac.disasm(str(path),row['code'],row['code'],row['code']+row['size']))
  # Decoder les copies finales hors des plages historiques, notamment ACID et
  # HALL. Le decodeur est idempotent si un banc specialise les installe aussi.
  extra=[]
  for key in ('fundamentals','punch','legacy'):
   d=m.get(key)
   if d:extra.append((key,d['code'],d['code_bytes']))
  hall=m.get('audio_headroom',{}).get('hall')
  if hall:extra.append(('hall',hall['code'],hall['end']-hall['code']))
  import hashlib
  folder=ROOT/'tmp/emu-runtime-code';folder.mkdir(parents=True,exist_ok=True)
  for label,at,n in extra:
   code=bytes(e.uc.mem_read(at,n));path=folder/(label+'-'+hashlib.sha256(code).hexdigest()+'.bin')
   if not path.exists():path.write_bytes(code)
   e.emac.install(emac.disasm(str(path),at,at,at+n))
  def stub(u,pc,size,data):
   sp=u.reg_read(C.UC_M68K_REG_A7);u.reg_write(C.UC_M68K_REG_D0,0);u.reg_write(C.UC_M68K_REG_PC,int.from_bytes(u.mem_read(sp,4),'big'));u.reg_write(C.UC_M68K_REG_A7,sp+4)
  if not native_chordkeys:
   for n in ['ck_audio_config','ck_audio_locked_controls']:e.uc.hook_add(UC_HOOK_CODE,stub,begin=sy[n],end=sy[n])
  for t,machine in enumerate([0,7,2,6,11,5]):
   e.set(t,machine=machine,note=52+3*t,pitch=64,color=64,shape=64,sweep=64,contour=64,decay=100)
   e.uc.mem_write(sy['gv_gain']+4*t,struct.pack('>I',16777216));e.uc.mem_write(E.PARAMS+14+66*t+46,struct.pack('>3H',0,32512,0))
  e.set(0,color=10,shape=16,sweep=16,contour=24)
  e.set(1,color=16,shape=32,sweep=48,contour=32)
  e.set(2,color=46,shape=48,sweep=0,contour=20)
  e.set(3,color=0,shape=127,sweep=cutoff,contour=resonance)
  e.set(4,color=20,shape=15,sweep=70,contour=64,punch=2)
  e.set(5,color=3,shape=43,sweep=24,contour=64)
  # Slot mono charge, sine16 a48k ; stockage simule mais vrai sampler render.
  e.uc.mem_write(0x4a810040,struct.pack('>8192h',*[int(12000*math.sin(i*2*math.pi/100)) for i in range(8192)]))
  for k,v in [('slot_base',0x4a810000),('slot_count',8192),('slot_size',16448),('slot_pgain',0x10000)]:
   if k in sy:e.uc.mem_write(sy[k],struct.pack('>I',v))
  e.uc.mem_write(sy['track_slot']+3*4,struct.pack('>I',0));e.count=0
  if stereo:
   e.uc.mem_write(0x4a814040,struct.pack('>8192h',*[int(4000*math.sin(i*2*math.pi/71)) for i in range(8192)]))
   e.uc.mem_write(sy['slot_soff'],struct.pack('>I',16384));e.uc.mem_write(sy['chn_sel']+12,struct.pack('>I',1))
  e.filter_hits=0
  def hit(u,pc,size,data,e=e):e.filter_hits+=1
  e.uc.hook_add(UC_HOOK_CODE,hit,begin=0x401ad3d8,end=0x401ad3d8)
  def count(u,pc,size,data,e=e):e.count+=1
  if audit_count:e.uc.hook_add(UC_HOOK_CODE,count)
  e.audit_symbols=sy
  engines.append(e)
 return engines

def check(stereo,cutoff,resonance):
 engines=fixtures(stereo,cutoff,resonance)
 peaks=np.zeros(6,dtype=np.int64);different=0
 for b in range(16):
  outs=[e.block(63 if b%8==0 else 0) for e in engines]
  for t in (0,1,2,4,5):assert np.array_equal(outs[0][t],outs[1][t]),('other voice',t,b)
  if cutoff==127:assert np.array_equal(*outs),('bypass',b)
  else:different+=not np.array_equal(outs[0][3],outs[1][3])
  peaks=np.maximum(peaks,np.max(np.abs(outs[1]),axis=1))
 assert peaks[3]>1000 and not any(e.unmapped for e in engines),(peaks.tolist(),[e.unmapped for e in engines])
 if cutoff==127:assert [e.filter_hits for e in engines]==[0,0]
 else:assert different and all(e.filter_hits==16*(2 if stereo else 1) for e in engines),[e.filter_hits for e in engines]
 print('PASS vrai lecteur PCM Wizard', 'stereo' if stereo else 'mono','cutoff/res',cutoff,resonance,'hits',[e.filter_hits for e in engines],'; bypass exact ou filtre actif, autres voix exactes, retriggers et zero acces non mappe',flush=True)

def main():
 for stereo in (False,True):
  for cutoff,res in ((127,0),(70,100)):check(stereo,cutoff,res)
if __name__=='__main__':main()
