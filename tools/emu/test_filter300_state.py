"""Regression3.00 : stockage par pattern/projet et course resonance sur le code natif."""
from pathlib import Path
import argparse,inspect,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
import boot_candidate as bc
import test_fx_menu_control as fx
from unicorn import m68k_const as C
m=json.loads((a.build/'BUILD.json').read_text());d=m['filter_pattern300'];s=d['symbols'];al=d['aliases'];bc.ROOT=a.output.parent/'cache';fx.metadata=m;fx.boot=lambda path:bc.boot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata');exec(src,fx.__dict__)
def fixture(saved=None):
 r,_,held,log,files,key,turn,data,bind=fx.fixture('unused');files.update(saved or {})
 r.u.mem_map(0x80000000,0x20000)
 for off,at,n in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):r.u.mem_write(at,bytes(r.u.mem_read(0x46700000+off,n)))
 bind(0x40000542,lambda a:0);r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000);r.call(m['complete_irq_accounting']['boot_target']);r.u.reg_write(C.UC_M68K_REG_SR,0x2000)
 for h in d['late_hooks']:assert bytes(r.u.mem_read(h['at'],6))==b'\x4e\xf9'+struct.pack('>I',h['target'])
 root,owner,pattern=0x931c0000,0x42000000,0x42010000;r.w32(0x40fe4228,root);r.w32(root+16,owner);r.w32(owner+8,123);r.w32(0x40a7887c,pattern);r.w32(pattern+30706,0);bind(al['fp_quiet'],lambda a:1);r.call(s['fp_frame'])
 return r,files,bind,pattern,data
legacy=bytes([70,67,1,6,1,1,1,1,1,1,254,254,254,254,254,254,165,90])
r,files,bind,pattern,data=fixture({'/Filter.cfg':legacy})
def modes():return [r.call(0x468d0110,t) for t in range(6)]
assert modes()==[0]*6,'global HP contaminated an unconfigured pattern'
for t in range(6):r.call(0x468d0120,t,t%4)
expected=[t%4 for t in range(6)];expected_modes=list(expected);r.call(s['fp_frame']);assert '/F3p_0000007b.cfg' in files;assert files['/Filter.cfg']==legacy
r.w32(pattern+30706,1);assert modes()==[0]*6
r.call(0x468d0120,0,3);assert modes()==[3,0,0,0,0,0]
r.w32(pattern+30706,0);assert modes()==expected
# Copie de pattern, presse-papiers et clear : memes signatures natives.
base=0x42000000+28;clip=0x931e0000
r.u.mem_write(base,bytes((i*31+7)&255 for i in range(30710)));r.u.mem_write(base+2*30710,b'\x5a'*30710)
r.call(s['fp_copy'],base+2*30710,base,30710)
assert bytes(r.u.mem_read(base+2*30710,30710))==bytes(r.u.mem_read(base,30710)),'native pattern bytes changed'
bind(s['fp_old_copy'],lambda args:77);bind(s['fp_old_init'],lambda args:79)
assert r.call(s['fp_copy'],base+2*30710,base,30710)==77
r.w32(pattern+30706,2);assert modes()==expected
assert r.call(s['fp_copy'],clip,base+2*30710,30710)==77
assert r.call(s['fp_init'],base+2*30710,0)==79;assert modes()==[0]*6
assert r.call(s['fp_copy'],base+2*30710,clip,30710)==77;assert modes()==expected
r.w32(pattern+30706,0);assert modes()==expected
r.call(s['fp_frame']);saved=dict(files)
r2,f2,b2,p2,data2=fixture(saved);assert [r2.call(0x468d0110,t) for t in range(6)]==expected
r2.w32(p2+30706,1);assert [r2.call(0x468d0110,t) for t in range(6)]==[3,0,0,0,0,0]
for payload in (b'',b'garbage',saved['/F3p_0000007b.cfg'][:-1],saved['/F3p_0000007b.cfg']+b'x'):
 bad=dict(saved);bad['/F3p_0000007b.cfg']=payload;rr,ff,bb,pp,dd=fixture(bad);assert [rr.call(0x468d0110,t) for t in range(6)]==[0]*6
# Changement de projet : aucun type du projet sortant dans le nouveau.
r2.w32(0x42000008,456);r2.w32(al['fp_generation'],1);r2.call(s['fp_frame']);assert [r2.call(0x468d0110,t) for t in range(6)]==[0]*6
print('PASS pattern isolation, reload, project isolation, corrupt files and legacy global HP ignored')
# Conversion native exacte, puis les deux nouveaux producteurs de coefficients.
rows=[]
for fn in ('fast_pf_coeff','fast_fc_coeff'):
 values=[]
 for res in (0,16,32,48,64,80,96,112,127):
  r.u.mem_write(data+48,struct.pack('>2H',64<<8,res<<8));r.u.reg_write(C.UC_M68K_REG_A2,data);r.u.reg_write(C.UC_M68K_REG_D2,0);r.u.reg_write(C.UC_M68K_REG_D1,0);r.call(0x401bad48)
  native=r.r32(0x401bbd7c);ptr=r.call(s[fn],0);q=r.r32(ptr+4);assert q==min(native,15000)
  values.append((res,native,q,bytes(r.u.mem_read(ptr+8,12)).hex()))
 assert len({v[3] for v in values})==len(values),'resonance upper range still clipped'
 rows.append(dict(function=fn,values=values))
print('PASS native resonance conversion: all nine panel positions produce distinct coefficients in LOW and multimode kernels')
# Courbe entiere : coefficients Q30 contre les fractions entieres de reference.
cases=0
for mode in (0,1,2):
 r.w32(al['fc_type'],mode)
 for f in (1,17,256,1024,2048,3072,4095):
  for native in range(0,15001,120):
   r.w32(0x401bbd60,f);r.w32(0x401bbd7c,native);q=native*8191//15000;c=4096-f;ff=f*f;cc=c*c;feedback=((362-(q*346>>13))*f*c)>>8;den=ff+cc+feedback;diff=ff-cc
   expected=(((ff if mode==0 else cc if mode==1 else feedback)<<30)//den,(1 if diff>=0 else -1)*2*((abs(diff)<<30)//den),((ff+cc-feedback)<<30)//den)
   ptr=r.call(s['fast_fc_coeff'],0);actual=struct.unpack('>3i',r.u.mem_read(ptr+8,12));assert actual==expected,(mode,f,native,actual,expected);cases+=1
# Transitions uniquement : aucun nouveau detour dans le dispatch audio par piste.
assert all(h['at']!=m['filter_modes']['symbols']['fc_dispatch'] for h in d['late_hooks'])
for t,v in enumerate(expected_modes):r.w32(al['fc_type']+4*t,v)
r.w32(pattern+30706,1)
bind(s['fp_old_lfosync'],lambda args:0);r.call(s['fp_lfosync'],0,0);assert [r.r32(al['fc_type']+4*t) for t in range(6)]==[3,0,0,0,0,0]
def changed(args):r.w32(pattern+30706,0);return 0
bind(s['fp_old_change'],changed);r.call(s['fp_change'],pattern);assert [r.r32(al['fc_type']+4*t) for t in range(6)]==expected_modes
print('PASS',cases,'Q30 coefficient cases and pattern-transition hooks without per-track DSP dispatch')

# Un changement pendant une ecriture ne doit pas etre marque sauvegarde.
r.call(s['fp_set'],0,1);write=r.stubs[0x4007bb0a];armed=[True]
def concurrent_write(args):
 result=write(args)
 if armed[0]:
  armed[0]=False;r.w32(al['fc_type'],2);r.u.mem_write(s['bank'],b'\x02');r.w32(s['revision'],r.r32(s['revision'])+1)
 return result
bind(0x4007bb0a,concurrent_write);r.call(s['fp_frame']);assert r.r32(s['dirty'])==1
bind(0x4007bb0a,write);r.call(s['fp_frame']);assert r.r32(s['dirty'])==0
print('PASS save interrupted by state change stays dirty and is retried')

a.output.write_text(json.dumps(dict(source=m['sha256'],pattern_state=True,project_state=True,reload=True,corrupt_file_defaults=True,resonance=rows,coefficient_reference_cases=cases,no_per_track_dsp_hook=True,concurrent_save_retry=True,hardware_tested=False),indent=2)+'\n')
