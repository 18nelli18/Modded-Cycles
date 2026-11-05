"""GOV : vrais classement/regulateur, menu natif et sauvegarde globale bornee."""
from pathlib import Path
import sys,json,struct,random
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
import argparse
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,default=ROOT.parent/'gov-policy372/proof-build');p.add_argument('--capture',type=Path);a=p.parse_args();b=a.capture or a.build;m=json.loads((a.build/'BUILD.json').read_text());d=m['gov_policy372'];s=d['symbols'];al=d['aliases'];r=Rig((b/'native.bin').read_bytes(),{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in s.items()}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,(b/'runtime.bin').read_bytes());u.mem_map(0x80000000,0x20000);u.mem_write(0x80000000,(b/'sram.bin').read_bytes())
def bind(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
# D0 piste, D2 cle ; les autres arguments restent ceux du noyau natif.
g=m['governor_key_optimization'];gains=[];p=g['gain_list']
while (v:=r.r32(p)):
 gains.append(v);p+=4;assert len(gains)<=16
for a in gains:
 for t in range(6):r.w32(a+4*t,0x20000000)
rng=random.Random(372)
for i in range(120):
 t=i%6;u.mem_write(0x80001858+128*t,struct.pack('>32i',*[rng.randrange(-2**30,2**30) for _ in range(32)]))
 u.reg_write(C.UC_M68K_REG_D0,t);r.call(g['target']);expected=u.reg_read(C.UC_M68K_REG_D2)
 r.w32(s['gp_mode'],0);u.reg_write(C.UC_M68K_REG_D0,t);r.call(g['original_entry']);assert u.reg_read(C.UC_M68K_REG_D2)==expected
 r.w32(s['gp_mode'],1);u.reg_write(C.UC_M68K_REG_D0,t);r.call(g['original_entry']);assert u.reg_read(C.UC_M68K_REG_D2)==t and u.reg_read(C.UC_M68K_REG_D0)==t
 if m.get('gov_inv_master380'):
  r.w32(s['gp_mode'],2);u.reg_write(C.UC_M68K_REG_D0,t);r.call(g['original_entry']);assert u.reg_read(C.UC_M68K_REG_D2)==5-t and u.reg_read(C.UC_M68K_REG_D0)==t
GB=0x46732000
def govern(mode,protected=(),young=(),stolen=()):
 u.mem_write(GB,bytes(0x1200));r.w32(GB+0x7c,280);r.w32(GB+0xf08,100);r.w32(s['gp_mode'],mode)
 for t in range(6):
  u.mem_write(GB+0x3a+2*t,struct.pack('>H',0 if t in young else 80));r.w32(GB+0xa+4*t,1000000)
  u.mem_write(0x80001858+128*t,struct.pack('>32i',*([(6-t)*1000000]*32)))
  if t in protected:u.mem_write(GB+4+t,b'\1')
  if t in stolen:u.mem_write(GB+0x4c+t,b'\1')
 u.reg_write(C.UC_M68K_REG_A1,GB);u.reg_write(C.UC_M68K_REG_D2,90112);u.reg_write(C.UC_M68K_REG_D4,256);u.reg_write(C.UC_M68K_REG_D5,280);r.call(0x8000e794)
 return [t for t,x in enumerate(u.mem_read(GB+0x58,6)) if x]
assert govern(0)==[5]
assert govern(1)==[0]
assert govern(1,protected=(0,))==[1]
assert govern(1,young=(0,1))==[2]
assert govern(1,stolen=(0,))==[1]
if m.get('gov_inv_master380'):
 assert govern(2)==[5]
 assert govern(2,protected=(5,))==[4]
 assert govern(2,young=(5,4))==[3]
 assert govern(2,stolen=(5,))==[4]
 for i in range(6):
  assert govern(1,stolen=tuple(range(i)))==[i]
  assert govern(2,stolen=tuple(range(6-i,6)))==[5-i]
 assert govern(2,protected=tuple(range(6)))==[]
 print('PASS INV native: 6/5/4/3/2/1, TRK 1/2/3/4/5/6; same eligibility guards')
print('PASS native governor: Lod quietest, Trk lowest index; protected/young/stolen voices skipped')
# Menu/data/back, avec delegation du reste de l arbre.
delta=[0];delegated=[];bind(0x4006f73a,lambda a:delta[0]);bind(0x40076bee,lambda a:0);bind(s['gp_old_edit'],lambda a:0);bind(s['gp_old_key'],lambda a:delegated.append(('key',r.r32(al['gc_tree_cursor']))) or 71);bind(s['gp_old_encoder'],lambda a:delegated.append(('encoder',r.r32(al['gc_tree_cursor']))) or 72);bind(s['gp_old_frame'],lambda a:0)
for k in ('menu','gc_level'):r.w32(al[k],1)
for k in ('gc_page','sx_submenu','du_page','mq_page'):r.w32(al[k],0)
r.w32(al['gc_tree_cursor'],0);event=0x931d0000
def key(k,f):u.mem_write(event,struct.pack('>6I',0x400fc20c,0,0,k,f,0));return r.call('gp_key',event)
def turn(v):delta[0]=v;u.mem_write(event,struct.pack('>6I',0x400fbebc,0,0,1,v&0xffffffff,0));return r.call('gp_encoder',event)
r.w32(s['gp_mode'],1)
turn(-1);assert r.r32(al['gc_tree_cursor'])==d['global_row'];key(32,1);key(32,16);assert r.call('gp_edit')==1
turn(-1);assert r.r32(s['gp_mode'])==0;turn(1);assert r.r32(s['gp_mode'])==1;key(12,1);key(12,16);assert r.call('gp_edit')==0
turn(1);assert r.r32(al['gc_tree_cursor'])==0
r.w32(al['gc_tree_cursor'],4);assert turn(1)==72
objects=[];bind(0x400423e4,lambda a:objects.append(a[0]) or 0);r.call('gp_global_draw',0,0x931c0000);obj=objects[-1];vt=r.r32(obj);assert r.call(r.r32(vt+12),obj)==d['global_rows'];labels=[]
for i in range(d['global_rows']):
 u.reg_write(C.UC_M68K_REG_A0,0x931f0000);r.call(r.r32(vt+16),obj,i);item=r.r32(0x931f0000);labels.append(r.string(r.r32(item+12)))
expected=['Pad','Mac','USB','Num','Mute','Dly','DX','QntM','Grv','LFOs']+([] if m.get('hide_master_fx382') else ['FX'])+(['ACID'] if m['activity_masks']['full'] else [])+['JUMP','GOV']
assert labels==expected,labels
if m.get('hide_master_fx382'):
 def parent_navigation(args):
  cursor=r.r32(al['gc_tree_cursor']);r.w32(al['gc_tree_cursor'],(cursor+(1 if delta[0]>0 else -1))%d['global_row']);return 72
 bind(s['gp_old_encoder'],parent_navigation)
 r.w32(al['gc_tree_cursor'],9)
 turn(1);assert r.r32(al['gc_tree_cursor'])==11
 turn(-1);assert r.r32(al['gc_tree_cursor'])==9
 for direction in (1,-1):
  for i in range(2*d['global_rows']):
   visible=[v for v in range(d['global_row']+1) if v!=10];prior=r.r32(al['gc_tree_cursor'])
   turn(direction);assert r.r32(al['gc_tree_cursor'])==visible[(visible.index(prior)+direction)%len(visible)]
 r.w32(al['gc_tree_cursor'],d['global_row'])
 r.call('gp_global_draw',0,0x931c0000)
 assert r.call(m['hide_master_fx382']['symbols']['mr_row'])==d['global_rows']-1
values=[];bind(0x40072260,lambda a:0);bind(0x40072080,lambda a:0);bind(0x40071a04,lambda a:values.append(r.string(a[6])) or 0)
for mode in (0,1):r.call('gp_set',mode);r.call('gp_value',0,0,0x931c0000,122,32)
assert values==['Lod','Trk']
if m.get('gov_inv_master380'):
 r.w32(al['gc_tree_cursor'],d['global_row']);key(32,1);key(32,16)
 turn(1);assert r.r32(s['gp_mode'])==2
 turn(1);assert r.r32(s['gp_mode'])==2
 turn(-1);assert r.r32(s['gp_mode'])==1
 turn(-1);assert r.r32(s['gp_mode'])==0
 turn(-1);assert r.r32(s['gp_mode'])==0
 r.call('gp_set',2);r.call('gp_value',0,0,0x931c0000,122,32);assert values[-1]=='INV'
# E/S simulees : octets du format reel, pas d ecriture en lecture.
files={};handle=[None];position=[0]
def fopen(a):
 path=r.string(a[0]);mode=r.string(a[1])
 if mode=='r' and path not in files:return 1
 if mode=='w':files[path]=bytearray()
 handle[0]=path;position[0]=0;return 0
def fread(a):
 data=files[handle[0]][position[0]:position[0]+a[1]];u.mem_write(a[0],bytes(data));position[0]+=len(data);return len(data)
def fwrite(a):files[handle[0]].extend(u.mem_read(a[0],a[1]));return a[1]
bind(0x4007bc5e,fopen);bind(0x4007baaa,fread);bind(0x4007bb0a,fwrite)
for at in (0x4007bc1c,0x4007bb76,0x4007e2f6):bind(at,lambda a:0)
bind(al['gc_input_quiet'],lambda a:1)
r.w32(0x40a7883c,1);r.w32(0x40a78874,1);r.call('gp_service');assert not files
saved_mode=2 if m.get('gov_inv_master380') else 1
r.w32(0x40a7883c,0);r.w32(0x40a78874,0);r.call('gp_service');assert bytes(files['/Governor.cfg'])==bytes([71,86,1,1,saved_mode,255-saved_mode,165,90])
for k in ('loaded','changed','dirty'):r.w32(s[k],0)
r.w32(s['gp_mode'],0);r.call('gp_service');assert r.r32(s['gp_mode'])==saved_mode
for bad in (b'',bytes([71,86,1,1,3,252,165,90]),bytes([71,86,1,1,1,0,165,90])):
 files['/Governor.cfg']=bytearray(bad)
 for k in ('loaded','changed','dirty'):r.w32(s[k],0)
 r.w32(s['gp_mode'],0);r.call('gp_service');assert r.r32(s['gp_mode'])==0
(b/'proof.json').write_text(json.dumps(dict(Lod_keys_exact=120,track_order_native=True,eligibility_retained=True,native_menu_labels=labels,storage_deferred=True,powercycle_load=True,invalid_files_rejected=True,hardware_tested=False),indent=2))
print('PASS native14-row Global UI, DATA/BACK/navigation, deferred save, power-cycle reload and corrupt-file rejection')
