"""v84 : S de US moins grave/granuleux, enveloppes et duree/pitch conserves."""
import sys,struct,json,wave
import numpy as np
from boot_candidate import ROOT
from test_vinyl_dust import rig,IN,OUT
from test_fx_cpu import counted
NEW=sys.argv[1]
def render(stem,word=8):
 r,_,m=rig(stem);s=m['speak']['symbols'];state=IN+2048;inp=IN+3072;r.u.mem_write(state,bytes(r.r32(s['speak_state_bytes'])));r.u.mem_write(inp,struct.pack('>7i',60<<16,64,word,64,80,0,1));audio=[]
 for b in range(2000):
  r.call(s['speak_block'],state,inp,OUT);audio.extend(struct.unpack('>32i',r.u.mem_read(OUT,128)));r.w32(inp+24,0)
  if r.r32(state+24):break
 return np.array(audio,dtype=np.float64)/16384,b+1

def bands(y,lo,hi):
 x=y[int(lo*48000):int(hi*48000)];p=abs(np.fft.rfft(x*np.hanning(len(x))))**2;hz=np.fft.rfftfreq(len(x),1/48000)
 return dict(low=float(p[hz<1600].sum()),high=float(p[(hz>2200)&(hz<3900)].sum()),rms=float(np.mean(x*x)**.5))

def main():
 rows=[];clips=[]
 for stem in ('validation/all-features-polivoks-cpu-trim-test-v82','validation/all-features-polivoks-cpu-trim-test-v83',NEW):
  y,n=render(stem);vowel=bands(y,.055,.11);s=bands(y,.15,.23);rows.append(dict(candidate=stem,blocks=n,vowel=vowel,s=s));clips.append(y)
  print('MEASURE US',rows[-1],flush=True)
 assert len({r['blocks'] for r in rows})==1
 assert 1.85<rows[2]['vowel']['rms']/rows[0]['vowel']['rms']<2.1,'vowel loudness not retained'
 for old in rows[:2]:
  assert rows[2]['s']['low']<old['s']['low']*.5,'S low/mid rasp not reduced'
  assert rows[2]['s']['high']/rows[2]['s']['low']>old['s']['high']/old['s']['low']*3,'S not more hiss-like'
 assert rows[2]['s']['rms']>20,'S disappeared'
 # Preview identique de niveau : v82 remis au gain nominal v83/v84.
 path=ROOT/'output/firmware/validation'/('speak-us-82-83-'+NEW.rsplit('-',1)[-1]+'.wav');combined=[]
 for i,y in enumerate(clips):combined.extend(y*(2 if i==0 else 1));combined.extend([0]*12000)
 with wave.open(str(path),'wb') as w:w.setparams((1,2,48000,0,'NONE','not compressed'));w.writeframes(np.clip(combined,-32768,32767).astype('<i2').tobytes())
 (ROOT/'output/firmware'/('speak-consonants-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(dict(rows=rows,preview=str(path),hardware_tested=False),indent=2)+'\n')
 print('PASS US: lower low-mid S energy versus82 and83, upper hiss retained, same duration, louder vowel retained',flush=True)
if __name__=='__main__':main()
