"""v81+ : callbacks chorus perimees pendant lecture, Size/Tone natifs immediats."""
import sys,json,struct
from boot_candidate import ROOT
from test_stereo_chorus_popup import rig
NEW=sys.argv[1]
def main():
 results=[]
 for stem in ('staging/all-features-polivoks-cpu-trim-test-v80',NEW):
  m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());s=m['stereo_chorus']['symbols'];u=rig(stem)
  u.uc.mem_write(s['ch_mode'],struct.pack('>I',1));u.call(s['ch_labels']);fmt=struct.unpack('>2I',u.uc.mem_read(s['saved_format'],8));rows=[]
  for mode in (0,3,7,0):
   # Aucune actualisation ch_labels : reproduit une selection en lecture.
   u.uc.mem_write(s['ch_mode'],struct.pack('>I',mode))
   for j,desc in enumerate((39,40)):
    for value in (0,1,63,64,65,126,127):
     obj=0x40a71754+desc*100+20;buf=0x931f0000
     u.call(fmt[j],obj,value<<8,buf);native=u.cstr(buf)
     u.call(s['ch_format'],obj,value<<8,buf);actual=u.cstr(buf)
     if stem==NEW:assert actual==native,(mode,desc,value,native,actual)
     rows.append((desc,value,native,actual))
  if stem!=NEW:assert any(a!=b for d,v,a,b in rows),'v80 failure not reproduced'
  else:
   for mode in (1,2):
    u.uc.mem_write(s['ch_mode'],struct.pack('>I',mode))
    for desc in (39,40):
     u.call(s['ch_format'],0x40a71754+desc*100+20,64<<8,0x931f0000);assert u.cstr(0x931f0000)=='64'
  results.append(rows);print('PASS formatter',stem,'native extremes',[(d,v,a) for d,v,a,b in rows[:14] if v in (0,64,127)],flush=True)
 print('PASS v80 stale chorus formatting reproduced; immediate native Size/Tone including INF and bipolar Tone; chorus numbers retained',flush=True)
if __name__=='__main__':main()
