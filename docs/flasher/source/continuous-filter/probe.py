"""Reproduire la rupture par reset de voix dans le vrai ladder partagé."""
import json,struct,copy
import build,test_lfo_plus as C
from chord_keys_pr87 import load_stock
P='work/wizard-filter-continuous/';w=json.load(open('work/sample-wizard-main/installer.json'));s={k:int(v,16) for k,v in w['symbols'].items()};stock=load_stock('firmware/model-cycles_OS1.13.syx');img,_=build.apply_writes(stock,[w]);raw=build.payload_runtime(w,stock,None);base=int(w['append']['dest'],16);at=s['gflt_run'];i=at-base;body=raw[i:i+160];n=14;needle=body[n:n+8];assert needle[:2]==b'\x41\xfa' and needle[4:]==bytes.fromhex('20700c00');assert at+n+2+struct.unpack('>h',needle[2:4])[0]==s['voice_ptr'];fix=dict(off=i+n,old=needle.hex(),new=(b'\x4e\xf9'+struct.pack('>I',s['gr2_nt'])+b'\x4e\x71').hex());print('Guarded reset branch',hex(base+fix['off']),fix)
runs=[]
for mode in ['original-reset','continuous']:
 code=bytearray(raw)
 if mode=='continuous':code[fix['off']:fix['off']+len(bytes.fromhex(fix['old']))]=bytes.fromhex(fix['new'])
 r=C.Rig(img,[(base,bytes(code))]);frame=C.FAKE+0x10000;voice=C.FAKE+0x20000;buf=C.FAKE+0x30000;r.w32(s['voice_ptr'],voice);r.w16(frame+48,0x3800);r.w16(frame+50,0)
 r.call(s['gflt_coef'],regs={C.D[1]:0,C.D[2]:0,C.A[2]:frame});allout=[]
 for blk in range(150):
  r.w32(voice+56,1);r.uc.mem_write(buf,struct.pack('>32i',*([0x18000000]*32)));r.call(s['gflt_run'],buf,0,check='ladder ABI');allout+=list(struct.unpack('>32i',r.rd(buf,128)))
 edges=[abs(allout[i]-allout[i-1]) for i in range(32,len(allout),32)];runs.append((allout,edges));assert not C.FAIL and not r.bad,(C.FAIL,r.bad)
 print(mode,'max boundary jump',max(edges),'last',edges[-1],'level',allout[-1])
assert max(runs[0][1])>0x100000 and max(runs[1][1][100:])==0
open(P+'reset-fix.json','w').write(json.dumps(fix));print('PASS reproduced block-edge discontinuity; continuous history settles without periodic resets')
