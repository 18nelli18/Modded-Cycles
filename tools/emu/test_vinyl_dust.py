"""Poussiere v58 : PCM ColdFire exact, silence d entree, spectre et preview natif."""
import sys,json,struct,math,wave,hashlib,time
from pathlib import Path
import numpy as np
from boot_candidate import ROOT,boot
from test_seq_gen_menu import Rig
IN=0x93190000;OUT=0x93190200

def rig(stem):
 m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));s=m['fx_menu']['symbols'];r=Rig(im,{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in s.items()}});r.u.mem_map(0x46700000,len(mem[0][1]));r.u.mem_write(*mem[0])
 if m['fx_menu'].get('idle_opt'):
  import emac
  from emac_state import ExtendedEMAC
  d=m['fx_menu'];r.mac=ExtendedEMAC(r.u)
  r.mac.install(emac.disasm(str(ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-',1)[-1]+'/fx.bin')),d['code'],d['code'],d['code']+d['code_bytes']))
  if d.get('ps1_fast_opt'):
   at=d['ps1_hot_address'];r.mac.install(emac.disasm(str(ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-',1)[-1]+'/ps1-hot.bin')),at,at,at+d['ps1_hot_code_bytes']))
 return r,s,m
class Ref:
 def __init__(self):self.seed=[0x5a17c9e3,0xc41d8b27];self.pop=[0,0];self.low=[0,0];self.slow=[0,0];self.gain=[0,0]
 def rnd(self,c):
  x=self.seed[c];x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff;self.seed[c]=x;return x
 def sample(self,c,a):
  if not a:self.pop[c]=self.low[c]=self.slow[c]=0;return 0
  r=self.rnd(c);r2=self.rnd(c);pulse=0
  if r&65535<4+3*a:
   amp=(8192+((r>>16)&65535))*a>>7;pulse=amp if r&65536 else -amp
  if r2&1048575<1+(a>>2):self.pop[c]=(65536+((r>>16)&65535))*a>>7
  if self.pop[c]:
   pulse+=(((r2>>20)-2048)*(self.pop[c]>>3))>>8;self.pop[c]-=self.pop[c]>>4
   if self.pop[c]<4:self.pop[c]=0
  self.low[c]+=(pulse-self.low[c])>>1;self.slow[c]+=(pulse-self.slow[c])>>3
  if not pulse and -2<self.low[c]<2:self.low[c]=0
  if not pulse and -8<self.slow[c]<8:self.slow[c]=0
  return (self.low[c]-self.slow[c])*12
 def block(self,signal,a,target=(16384,16384)):
  result=[]
  for i in range(32):
   for c in range(2):
    g=self.gain[c]+((target[c]-self.gain[c])*(i+1)>>5);noise=self.sample(c,a)*g>>15;x=(signal[2*i+c]>>11)+noise;result.append(max(-1048576,min(1048575,x))*2048)
  self.gain=list(target);return result

def reset(r,s,a,target=(16384,16384)):
 r.call('fx_vinyl_reset')
 for name,value in [('fx_crackle',a),('fx_warble',0),('fx_wspeed',0)]:r.w32(s[name],value)
 r.u.mem_write(s['dust_target'],struct.pack('>2I',*target));r.u.mem_write(s['dust_seed'],struct.pack('>2I',0x5a17c9e3,0xc41d8b27))
def block(r,signal):r.u.mem_write(IN,struct.pack('>64i',*signal));r.call('fx_vinyl',OUT,IN);return list(struct.unpack('>64i',r.u.mem_read(OUT,256)))
def wav(path,samples):
 a=np.array(samples,dtype=np.int64);a=np.clip(a>>16,-32768,32767).astype('<i2')
 with wave.open(str(path),'wb') as w:w.setparams((2,2,48000,0,'NONE','not compressed'));w.writeframes(a.tobytes())

def main():
 stem=sys.argv[1];r,s,m=rig(stem);report={};zero=[0]*64
 for amount in (0,24,64,127):
  reset(r,s,amount);ref=Ref();data=[]
  for b in range(256):
   sig=zero if b<128 else [int(140000000*math.sin((b*64+i)/13)) for i in range(64)]
   got=block(r,sig);expected=ref.block(sig,amount);assert got==expected,('PCM',amount,b,next((i for i in range(64) if got[i]!=expected[i]),None));data+=got[:64] if b<128 else []
  if amount==0:assert not any(data)
  else:assert any(data),'dust depends on input signal'
  report[str(amount)]={'pcm_sha256':hashlib.sha256(struct.pack('>'+str(len(data))+'i',*data)).hexdigest(),'zero_input_peak_q31':max(map(abs,data))}
 print('PASS1024 native blocks exact vs reference: crackle0/24/64/127 with silence and source',flush=True)
 # Chute du gain sous32 puis vers0 : aucune sous-transformation unsigned.
 reset(r,s,127,target=(1,31));ref=Ref()
 for b in range(4):assert block(r,zero)==ref.block(zero,127,(1,31))
 r.u.mem_write(s['dust_target'],bytes(8));assert block(r,zero)==ref.block(zero,127,(0,0));assert not any(block(r,zero))
 # Couche stationnaire sur8s d entree muette ; bouts de seconde tous actifs.
 reset(r,s,64);silence=[];start=time.monotonic()
 for b in range(12000):silence+=block(r,zero)
 y=np.array(silence,dtype=np.float64).reshape(-1,2)/2147483648.;assert all(np.any(part) for part in np.array_split(y,32)), 'noise not continuous through gaps'
 spectrum=np.abs(np.fft.rfft(y[:,0]))**2;hz=np.fft.rfftfreq(len(y),1/48000);ratio=float(spectrum[hz>=4000].sum()/spectrum.sum());assert ratio>.40,ratio
 assert abs(float(y.mean()))<1e-4;assert np.max(abs(y))<.5
 dest=ROOT/'output/firmware/validation';wav(dest/'vinyl-dust-v58b-isolated.wav',silence)
 # Preview au niveau reel : bref accord puis silence, meme poussiere continue.
 reset(r,s,64);audio=[]
 for b in range(12000):
  sig=[]
  for i in range(32):
   t=(b*32+i)/48000;v=0 if t>=4 else .045*sum(math.sin(2*math.pi*f*t) for f in (220,277.18,329.63))*(.6+.4*math.cos(2*math.pi*.5*t))
   sig.extend([int(v*2147483647)]*2)
  audio+=block(r,sig)
 wav(dest/'vinyl-dust-v58b-chord-and-gaps.wav',audio)
 report.update(stem=stem,sha256=m['sha256'],native_blocks=25029,high_band_fraction=ratio,noise_mean=float(y.mean()),noise_peak=float(np.max(abs(y))),render_seconds=time.monotonic()-start)
 (ROOT/'output/firmware/vinyl-dust-proof-v58.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS independent silence bed, exact zero-send ramp, high-band fraction',round(ratio,3),'native audio previews written',flush=True)
if __name__=='__main__':main()
