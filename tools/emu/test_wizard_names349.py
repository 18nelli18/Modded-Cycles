"""Reproduit le vrai override de popup puis verifie les quatre entrees UI."""
from pathlib import Path
s=Path(__file__).with_name('profile_voice_filter343.py').read_text().split('coefficients=Counter()')[0]
exec(compile(s,__file__,'exec'))
from wizard_names349 import apply,ENTRIES
from unicorn import UC_HOOK_CODE
selected=0;context=0x40812000;handle=0x40812100;vt=0x40812200;raw=0x40812300
def w(at,v):e.uc.mem_write(at,struct.pack('>I',v))
w(context,0x400fd134);w(context+4,handle);w(handle,vt);w(vt+40,0x40812400);e.uc.mem_write(raw+38,b'\x06')
def stub(uc,pc,*unused):
 sp=uc.reg_read(C.UC_M68K_REG_A7)
 if pc==0x400cf866:result=0x40810000
 elif pc==0x40012412:result=selected
 elif pc==0x40009c1a:result=handle if int.from_bytes(uc.mem_read(sp+8,4),'big')==selected else 0
 elif pc==0x400097f0:result=context
 else:result=raw
 uc.reg_write(C.UC_M68K_REG_D0,result);uc.reg_write(C.UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(C.UC_M68K_REG_A7,sp+4)
for at in [0x400cf866,0x40012412,0x40009c1a,0x400097f0,0x40812400]:e.uc.hook_add(UC_HOOK_CODE,stub,begin=at,end=at)
w(0x467aeb74+32,1)
def text(ptr):return bytes(e.uc.mem_read(ptr,40)).split(b'\0')[0].decode()
w(0x401b2554,3)
baseline=[text(e.call(ENTRIES['ld_long'][0],context,i)) for i in [73,74]]
if meta.get('wizard_names349'):
 assert baseline==['Density','Spray'],baseline
else:
 assert baseline==['Filter','Resonance'],baseline
 n=bytearray(e.uc.mem_read(0x40000400,0x1ffc00));r=bytearray(e.uc.mem_read(0x46700000,0x300000));d=apply(meta,n,r,W/'module')
 e.uc.mem_write(d['code'],bytes(r[d['code']-0x46700000:d['code']-0x46700000+d['code_bytes']]))
 for p in d['patches']:e.uc.mem_write(p['at'],bytes.fromhex(p['new']));e.uc.ctl_remove_cache(p['at'],p['at']+len(bytes.fromhex(p['new'])))
rows=[]
tables=[0x401ab88a]*3+[0x401ab916,0x401ab9a2,0x401aba2e,0x401ababa]
for selected in range(6):
 for mode,table in enumerate(tables):
  w(0x401b2554+selected*4,mode);w(0x401bc928+selected*4,0)
  for index,ident in enumerate([46,62,73,74]):
   for name,offset in [('ld_long',4),('ld_short',12)]:
    expected=int.from_bytes(e.uc.mem_read(table+28*index+offset,4),'big')
    actual=e.call(ENTRIES[name][0],context,ident);assert actual==expected,(selected,mode,name,index,text(actual),text(expected))
   expected=int.from_bytes(e.uc.mem_read(table+28*index+12,4),'big')
   assert e.call(ENTRIES['ld_first'][0],context,ident,0,index+11)==expected
   assert e.call(ENTRIES['ld_second'][0],index+11)==expected
  rows.append(dict(track=selected,mode=mode))
args.output.write_text(json.dumps(dict(baseline=baseline,cases=rows,entry_checks=672),indent=2)+'\n')
print('PASS baseline wrong popup reproduced; 672 long/short/primary/secondary name checks',flush=True)
