"""POTS : menu natif, stockage projet, DSP ColdFire et reset All Sound Off.

Les E/S fichiers et peripheriques DMA sont simules ; aucun resultat appareil.
"""
from pathlib import Path
import argparse, inspect, json, struct, subprocess, sys, textwrap
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--objdump',required=True)
a=p.parse_args();R=Path(__file__).resolve().parents[2];W=a.output.parent;W.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'tools/emu'),str(R/'tools')]
import boot_candidate as bc
bc.ROOT=W/'boot-cache'
import test_fx_menu_control as fx
from unicorn import m68k_const as C, UC_HOOK_MEM_INVALID
import emac
from emac_state import ExtendedEMAC
m=json.loads((a.build/'BUILD.json').read_text());path=next(a.build.glob('*.syx'))
fx.metadata=m;realboot=bc.boot;fx.boot=lambda _:realboot(path)
source=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata')
source=source.replace("**m['fx_menu']['symbols']","**m['fx_menu']['symbols'],**m['per_track_fx']['symbols']")
exec(compile(source,'pots-fixture','exec'),fx.__dict__)
r,s,h,log,files,key,turn,data,bind=fx.fixture('unused')
order=[11,10,9,12,5,0,1,2]
for mode in order:
 for sign in (-1,1):
  r.w32(s['cr_mode'],mode);key(2);turn(15,sign);turn(15,sign)
  assert r.r32(s['cr_mode'])==mode
  want=order[max(0,min(7,order.index(mode)+sign))]
  key(2,0);assert r.r32(s['cr_mode'])==want,(mode,sign,want,r.r32(s['cr_mode']))
r.w32(s['cr_mode'],12);key(2);turn(15);turn(15);key(12);key(12,0);key(2,0);assert r.r32(s['cr_mode'])==12
for mods in (set(),{1}):
 h.clear();h.update(mods);log.clear();turn(15);assert r.r32(s['cr_mode'])==12
 assert any(v[0]=='native' for v in log),log
h.clear();print('PASS menu huit positions, release, BACK et delegation Time/Feedback',flush=True)
for at in (0x40070efc,0x40070c4e,0x40070f6e):bind(at,lambda _:0)
rev=[10,11,8,7,0,1,2,9] if m.get('vinyl_removed') else m['fx_menu']['reverb_selector_order']
for slot,choices in ((0,rev),(1,order)):
 for cursor in range(len(choices)):
  for entry,args in (('nv_overlay',(0,0)),('nv_overlay_canvas',(0,))):
   r.w32(s['fx_menu_open'],1);r.w32(s['fx_menu_slot'],slot);r.w32(s['fx_menu_cursor'],cursor)
   r.texts.clear();r.call(entry,*args);labels=[t[2] for t in r.texts]
   if slot and cursor==3:assert 'POTS' in labels,labels
   if not slot and m.get('vinyl_removed'):assert not any('Vinyl' in t for t in labels)
r.w32(s['fx_menu_open'],0)
print('PASS les deux chemins de dessin ; Vinyl conserve seulement dans Optional',flush=True)
# Initialiser un vrai proprietaire et un UUID ; codec natif delegue uniquement.
root=0x41000000;holder=0x41300000;pattern=0x41400000
r.w32(0x40fe4228,holder);r.w32(holder+16,root);r.w32(root+8,0x12345678)
r.w32(0x40a7887c,pattern);r.w32(pattern+30706,0);r.w32(0x40fe4178,1)
bind(s['mf_old_frame'],lambda _:0);bind(s['mf_old_project_encode'],lambda _:1)
r.call('mf_frame');r.w32(s['cr_mode'],9)
r.w32(s['fx_menu_open'],1);r.w32(s['fx_menu_slot'],1);r.w32(s['fx_menu_cursor'],3)
r.call('mf_commit');assert r.r32(s['cr_mode'])==12
r.call('mf_project_encode',0,root,0,16,0)
saved=files['/MFX_12345678.cfg'];assert saved[16+37]==12 and len(saved)==4624
# Rechargement a froid du module, fichier conserve et ancien codec en Delay.
f=m['per_track_fx'];r.u.mem_write(f['bss'],bytes(f['bss_bytes']));r.w32(s['cr_mode'],0)
r.call('mf_frame');assert r.r32(s['cr_mode'])==12
r.call('mf_mode_set',1);assert r.r32(s['cr_mode'])==12
r.call('mf_choose',1,3,12);assert r.call('mf_choice',1,3)==12
r.call('mf_project_encode',0,root,0,16,0);assert files['/MFX_12345678.cfg'][16+39]==12
print('PASS sauvegarde projet, rechargement froid et choix TRK partage',flush=True)
# Executer le DSP reel avec les instructions EMAC exactes.
run=subprocess.run
def cross(argv,*pos,**kw):
 if isinstance(argv,list) and argv[0]=='m68k-linux-gnu-objdump':argv=[a.objdump,*argv[1:]]
 return run(argv,*pos,**kw)
subprocess.run=cross
raw=W/'pots-module.bin';raw.write_bytes(r.u.mem_read(f['code'],f['code_bytes']))
mac=ExtendedEMAC(r.u);mac.install(emac.disasm(str(raw),f['code'],f['code'],f['code']+f['code_bytes']))
IN=0x931a0000;OUT=IN+512;P=IN+1024
r.w32(0x40149310,14400);r.u.mem_write(P,struct.pack('>hh',0,96<<8))
line=f['pots_line'];size=f['pots_line_bytes'];r.u.mem_write(line,b'\xa5'*size)
r.u.mem_write(line-16,b'\x69'*16);r.u.mem_write(line+size,b'\x96'*16)
r.call('pots_reset');peaks=[]
for block in range(240):
 samples=[120000000]*64 if block==0 else [0]*64
 r.u.mem_write(IN,struct.pack('>64i',*samples));r.call('pots_process',OUT,IN,P)
 out=struct.unpack('>64i',r.u.mem_read(OUT,256));assert out[::2]==out[1::2]
 peaks.append(max(map(abs,out)))
assert max(peaks)>0 and max(peaks)<2147483647
assert bytes(r.u.mem_read(line-16,16))==b'\x69'*16 and bytes(r.u.mem_read(line+size,16))==b'\x96'*16
r.u.mem_write(IN,bytes(256));r.call(0x40059692,0);r.call('mf_fx_begin')
assert r.r32(s['st'])==1
r.call(0x40059692,1);r.call('mf_fx_begin');assert r.r32(s['st'])==0
for block in range(120):
 r.call('pots_process',OUT,IN,P);assert not any(r.u.mem_read(OUT,256)),block
print('PASS DSP stereo-mono, historique empoisonne, limites memoire et double STOP',flush=True)
# Le wrapper appelle aussi le vrai Delay natif pour preparer ses buffers.
r.u.mem_map(0x80000000,0x20000);r.u.mem_map(0xfc040000,0x10000);r.u.mem_map(0x4a000000,0x1000000)
runtime=W/'pots-runtime.bin';runtime.write_bytes(r.u.mem_read(0x46700000,f['end']-0x46700000))
old=m['fx_menu'];mac.install(emac.disasm(str(runtime),0x46700000,old['code'],old['code']+old['code_bytes']))
native=W/'pots-native.bin';native.write_bytes(r.u.mem_read(0x40057000,0x1200))
mac.install(emac.disasm(str(native),0x40057000,0x40057000,0x40058200))
r.u.hook_add(UC_HOOK_MEM_INVALID,lambda u,k,at,n,v,d:print('UNMAPPED',hex(at),hex(u.reg_read(C.UC_M68K_REG_PC)),flush=True) or False)
import test_seq_gen_menu as rig_module
init_source=textwrap.dedent(inspect.getsource(rig_module.Rig.call)).replace('def call(', 'def long_call(').replace('count=500000','count=8000000')
exec(init_source,rig_module.__dict__);rig_module.long_call(r,0x40057260)
r.w32(0x8000b570,0x8000a560)
for mode in (0,12,0,12,11,12,9,12,10,12,5,12,1,12,2):
 r.w32(s['cr_mode'],mode)
 for block in range(70):r.call('pots_slot_delay',OUT,IN,P,IN,IN)
 assert r.r32(s['pots_slot_active'])==int(mode==12)
 assert r.r32(s['pots_slot_gain'])==256 and r.r32(s['pots_slot_prior'])==256
 assert r.r32(s['cr_mode'])==mode
print('PASS transitions des sept anciens delays avec preparation DMA native',flush=True)
for time,feedback in ((0,0),(0,127),(127,0),(127,127)):
 r.u.mem_write(P,struct.pack('>hh',time<<8,feedback<<8));r.call('pots_reset')
 for block in range(32):
  signal=[2147483647 if (i+block)&1 else -2147483648 for i in range(64)]
  r.u.mem_write(IN,struct.pack('>64i',*signal));r.call('pots_process',OUT,IN,P)
 assert bytes(r.u.mem_read(line-16,16))==b'\x69'*16 and bytes(r.u.mem_read(line+size,16))==b'\x96'*16
r.w32(s['cr_mode'],12);r.w32(s['pots_slot_active'],1);r.w32(0x40149310,0)
r.call('pots_slot_delay',OUT,IN,P,IN,IN);assert not any(r.u.mem_read(OUT,256))
print('PASS entrees extremes, Time/Feedback aux bornes et garde tempo nul',flush=True)
report=dict(sha256=m['sha256'],menu_positions=16,project_save_cold_reload=True,shared_TRK=True,native_time_feedback=True,dsp_blocks=360,peak=max(peaks),first_echo_block=next(i for i,v in enumerate(peaks) if v),double_stop_clears=True,first_stop_preserves=True,ring_canaries=True,native_delay_transition_blocks=1050,hardware_tested=False)
a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS',report,flush=True)
