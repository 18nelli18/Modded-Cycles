"""185 : calculs LEGACY/ACID exacts et cout en instructions, sans mesure appareil."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
import emac
from unicorn import m68k_const as C
versions=['v152','v153'];es=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-'+v for v in versions],audit_count=False);ms=[]
for v,e in zip(versions,es):
 m=json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text());ms.append(m);d=m['legacy'];f=R/('output/firmware/governor-recovery-'+v+'/dx7.bin');e.emac.install(emac.disasm(str(f),d['code'],d['code'],d['code']+d['code_bytes']));e.count_instructions();e.emac.macsr=0xa0
 for i in range(4):e.emac.put_physical(i,0x123456789abc+i)
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
patches=bytes(es[0].uc.mem_read(ms[0]['legacy']['symbols']['dx7_default_bank'],4992));rows=[]
for case in range(8 if '--quick' in sys.argv else 70):
 p=bytearray(patches[156*(case%32):156*(case%32+1)])
 if case>=32:p[134]=(case-32)%32;p[135]=case%8;p[137]=99;p[138]=0;p[139]=99;p[140]=99;p[142]=case%6;p[143]=7;p[155]=63 if case<64 else [63,1,3,21,42,0][case%6]
 for e,m in zip(es,ms):
  e.uc.mem_write(0x40a71000,bytes(p));e.call(m['legacy']['symbols']['dx7_note_on'],0,0x40a71000,[0,24,48,72,96,127][case%6]<<16,[1,64,100,127][case%4])
 cost=[0,0]
 for b in range(8):
  outs=[];states=[]
  for i,(e,m) in enumerate(zip(es,ms)):
   s=m['legacy']['symbols'];e.call(s['dx7_controls'],0,([0,24,48,72,96,127][case%6]+(b//3))<<16,[0,64,127][b%3],[0,64,127][(b//2)%3],[0,64,127][(b//3)%3],int(b<6));e.instructions=0;e.call(s['dx7_block'],0,0x40a70000);cost[i]+=e.instructions;outs.append(bytes(e.uc.mem_read(0x40a70000,128)));size=int.from_bytes(e.uc.mem_read(s['dx7_track_bytes'],4),'big');states.append(bytes(e.uc.mem_read(s['_ZL10dx7_tracks'],size*6)));assert e.emac.macsr==0xa0 and all(e.emac.physical(k)==0x123456789abc+k for k in range(4))
  assert outs[0]==outs[1],('PCM',case,b)
  assert states[0]==states[1],('track state',case,b)
 row=dict(case=case,algorithm=p[134],instructions=cost,reduction=round(100*(1-cost[1]/cost[0]),3));rows.append(row);print('PASS LEGACY exact PCM/full track state',row,flush=True)
(W/'legacy153-profile.json').write_text(json.dumps(dict(rows=rows,hardware_tested=False),indent=2)+'\n')
