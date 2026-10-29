"""All Sound Off : PS1 au maximum, queues conservees au premier STOP et reset borne.
Les fonctions natives de commande sont executees ; les boutons physiques restent a tester.
"""
from pathlib import Path
import sys,json,struct,subprocess,argparse
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools/emu'),str(ROOT/'tools')]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build',type=Path,nargs='+',required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--objdump',required=True)
a=p.parse_args();W=a.output.parent;W.mkdir(parents=True,exist_ok=True)
import boot_candidate
boot_candidate.ROOT=W/'panic-context'
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
import emac
from emac_state import ExtendedEMAC
run=subprocess.run
def cross(argv,*pos,**kw):
 if isinstance(argv,list) and argv[0]=='m68k-linux-gnu-objdump':argv=[a.objdump,*argv[1:]]
 return run(argv,*pos,**kw)
subprocess.run=cross
rows=[]
for d in a.build:
 scope=d.parent.name;meta=json.loads((d/'BUILD.json').read_text());s={**meta['fx_menu']['symbols'],**meta['per_track_fx']['symbols']}
 image,mem=boot_candidate.boot(next(d.glob('*.syx')));r=Rig(image,{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in s.items()}})
 for at,data in mem:r.u.mem_map(at,len(data));r.u.mem_write(at,data)
 runtime=W/(scope+'-runtime.bin');runtime.write_bytes(mem[0][1]);mac=ExtendedEMAC(r.u)
 f=meta['fx_menu']
 for lo,size in [(f['code'],f['code_bytes']),(f['ps1_hot_address'],f['ps1_hot_code_bytes']),(meta['per_track_fx']['code'],meta['per_track_fx']['code_bytes'])]:mac.install(emac.disasm(str(runtime),0x46700000,lo,lo+size))
 IN=0x931a0000;OUT=IN+512;P=IN+1024;r.u.mem_write(IN,bytes(256));r.u.mem_write(P,struct.pack('>hh',32767,16384))
 r.w32(s['ch_mode'],7);r.w32(s['cr_mode'],0);r.w32(s['ps_filled'],2048);r.w32(s['ps_w'],0)
 r.u.mem_write(s['ps_comb'],struct.pack('>16448h',*([2400]*16448)));r.u.mem_write(s['ps_low'],struct.pack('>8i',*([2000]*8)))
 r.call('fx_ps1',OUT,IN,P);assert any(r.u.mem_read(OUT,256))
 # Le premier STOP/pause natif ne doit pas effacer la reverb.
 r.call(0x40059692,0);r.call('mf_fx_begin');assert r.r32(s['mf_fx_panic_count'])==0
 r.call('fx_ps1',OUT,IN,P);assert any(r.u.mem_read(OUT,256));assert r.r32(s['ps_filled'])==2048
 r.w32(s['lt_active'],0xf6);r.w32(s['lt_sent'],0xf6);r.u.mem_write(s['lt_bus'],b'\x12'*2048)
 before=bytes(r.u.mem_read(s['mf_live'],48));r.call(0x40059692,1);assert r.r32(s['mf_fx_panic_pending'])==1
 assert r.r32(s['mf_fx_panic_count'])==0
 count=[0];h=r.u.hook_add(UC_HOOK_CODE,lambda *a:count.__setitem__(0,count[0]+1));r.call('mf_fx_begin');r.u.hook_del(h)
 assert r.r32(s['mf_fx_panic_count'])==1 and r.r32(s['mf_fx_panic_pending'])==0
 assert r.r32(s['ps_filled'])==r.r32(s['lt_active'])==r.r32(s['lt_sent'])==0
 assert bytes(r.u.mem_read(s['mf_live'],48))==before and r.r32(s['ch_mode'])==7
 # Les octets de l'historique peuvent rester en RAM, mais jamais ressortir.
 for block in range(160):r.call('fx_ps1',OUT,IN,P);assert not any(r.u.mem_read(OUT,256)),('stale PS1 tail',scope,block)
 r.call('mf_fx_begin');assert r.r32(s['mf_fx_panic_count'])==1
 # L'autre setter All Sound Off est aussi capture, y compris repetitions.
 for value in (2,1,2):
  r.call(0x40058c04,value);assert r.r32(0x40a78e18)==value
  r.call('mf_fx_begin')
 assert r.r32(s['mf_fx_panic_count'])==4
 # Une nouvelle excitation reste audible apres la coupure.
 audible=False
 for block in range(180):
  signal=[180000000 if i%2==0 else -90000000 for i in range(64)] if block<8 else [0]*64
  r.u.mem_write(IN,struct.pack('>64i',*signal));r.call('fx_ps1',OUT,IN,P);audible|=any(r.u.mem_read(OUT,256))
 assert audible
 raw=bytes(r.u.mem_read(s['idle_voice_begin'],6));assert raw==b'\x4e\xb9'+struct.pack('>I',s['mf_fx_begin'])
 row=dict(scope=scope,first_stop_preserves_tail=True,all_sound_off_clears_ps1=True,silent_blocks_after_panic=160,new_input_recovers=True,repeated_panic_count=4,settings_preserved=True,reset_instructions=count[0]);rows.append(row);print('PASS',row,flush=True)
a.output.write_text(json.dumps(dict(cases=rows,hardware_tested=False),indent=2)+'\n')
