"""TRACK+COPY/PASTE natif : huit reglages LFO2, polarite et Undo, sans codec."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from unicorn import UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ,m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v215'
r,_,h,l,f,k,t,data,bind=fixture('staging/all-features-polivoks-cpu-trim-test-'+v);u=r.u
m=json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text());s=m['lfo_polarity']['symbols'];a=m['four_lfos']['aliases'];mx=m['four_lfos']['symbols']
r.call(0x4005a274);bind(0x400802ec,lambda a:0)
u.mem_map(0x93400000,0x400000);r.heap=0x93400000
allocs=[]
def alloc(args):
 size=args[0];at=r.new(args);guard=r.heap;r.heap+=16;u.mem_write(guard,b'\x5a'*16);allocs.append((at,size,guard));return at
bind(0x400802e0,alloc)
root=data+0x6000;table=data+0x10000;vt=data+0x20000;get=vt+0x100;notify=get+16;ctx=data+0x21000
r.w32(0x40fe4228,root);r.w32(0x40a78888,table);r.w32(a['lf2_context'],ctx);r.w32(a['lf2n_epoch'],0);r.w32(a['lf2n_seen'],0)
r.w32(vt+40,get);r.w32(vt+16,notify);bind(0x400cf866,lambda x:root);bind(0x4678eb16,lambda x:0)
handles_real=[r.call(0x40009c1a,root+116,t) for t in range(6)]
assert handles_real==[root+212+68*t for t in range(6)]
def handle(t):return handles_real[t]
def raw(t):return table+28+100*t
def settings(t):return ctx+192+16*t
for t in range(6):r.w32(handle(t),vt);r.w32(root+116+504+t*8+4,handle(t))
bind(get,lambda x:raw((x[0]-handle(0))//68));notified=[]
bind(notify,lambda x:notified.append(x[0]) or 0)
def seed(t,machine=0,flags=None):
 b=bytearray((i*37+t*19)&255 for i in range(100));b[38]=machine
 struct.pack_into('>5H',b,76,23000,0x400|(0xa0|flags if flags is not None else 0),0x200,0xb00,24576);u.mem_write(raw(t),bytes(b))
 u.mem_write(settings(t),struct.pack('>8H',23000,0x400|(0xa0|flags if flags is not None else 0),12000,0xb00,0x200,18000,0x300,24576))
 r.w32(s['lp_one']+4*t,1);r.w32(s['lp_two']+4*t,0)
def current(t):return bytes(u.mem_read(raw(t),100)),bytes(u.mem_read(settings(t),16))
# Real extra-bank initialization, hidden while the audio LFO count stays2.
u.mem_map(0x80000000,0x20000)
for t in range(6):u.mem_write(0x8000100c+16+66*t,struct.pack('>8H',0x7000,0x400,0x4000,0x7f00,0,0,0,0x4000))
from test_seq_gen_menu import STACK,STOP
from unicorn import m68k_const as C
def longcall(fn,*args):
 u.mem_write(STACK,struct.pack('>'+('I'*(len(args)+1)),STOP,*args));u.reg_write(C.UC_M68K_REG_A7,STACK);u.emu_start(fn,STOP,count=30000000);assert u.reg_read(C.UC_M68K_REG_PC)==STOP,(hex(fn),hex(u.reg_read(C.UC_M68K_REG_PC)));return u.reg_read(C.UC_M68K_REG_D0)
r.call=longcall
from unicorn import UC_HOOK_MEM_UNMAPPED
def fault(uc,access,address,size,value,data):print('FAULT',hex(address),'PC',hex(uc.reg_read(C.UC_M68K_REG_PC)),flush=True);return False
u.hook_add(UC_HOOK_MEM_UNMAPPED,fault)
rawproject=0x41400000;r.call(m['fx_project']['symbols']['fxp_new'],rawproject);r.w32(root+16,rawproject);pattern=rawproject+28;r.w32(0x40a7887c,pattern);bind(0x4000eae2,lambda a:r.r32(rawproject+8))
prepared=r.call(mx['mx_copy_prepare']);print('Unsaved project UUID',r.r32(rawproject+8),'bank ready',prepared,flush=True)
assert r.call(mx['mx_count_get'])==2


primary=struct.pack('>8H',0x7000,0x400,0x4000,0,0,0,0,0x4000)
secondary=struct.pack('>8H',0x7000,0x400,0x4000,0x7f00,0,0,0,0x4000)
extras=[r.r32(mx['mx_extra']+4*b) for b in range(2)]
def allstate(t):
 return (bytes(u.mem_read(raw(t)+22,16)),bytes(u.mem_read(settings(t),16)),*[bytes(u.mem_read(c+192+16*t,16)) for c in extras],r.r32(s['lp_one']+4*t),r.r32(s['lp_two']+4*t),*[r.r32(mx['mx_polarity']+4*(b*6+t)) for b in range(2)])
def seedall():
 for t in range(6):
  seed(t,machine=24,flags=3);u.mem_write(raw(t)+22,b'\x12\x00'*8);u.mem_write(0x40fde838+32*t,b'\x55'*32)
  for b,c in enumerate(extras):u.mem_write(c+192+16*t,struct.pack('>8H',19000,0x500,17000,0x1200,0x300,18000,0x200,29000));u.mem_write(c+32*t,b'\x55'*32);r.w32(mx['mx_polarity']+4*(b*6+t),1)

assert r.r32(rawproject+8)==0

assert prepared==1
xp=m['lfo_reload'];xs=xp['symbols'];xa={**xs,**xp['aliases']};r.w32(0x40fe4178,1);r.w32(0x40a7883c,0);r.w32(0x40a78874,0)
bind(xa['xp_quiet'],lambda args:1);bind(mx['mx_old_frame'],lambda args:0);bind(0x40012412,lambda args:0)
r.call(xs['xp_frame'])
# Reglages par les vrais setters UI, cache sonore sortant laisse intact.
r.call(mx['mx_select'],0)
for t in range(6):
 for field,value in enumerate((19000+t,5,17000+t,11,3,18000+t,2,29000+t)):assert r.call(a['lf2_edit'],ctx,t,field,value)==1
r.call(xs['xp_frame'])
def norm(t):
 vals=list(struct.unpack('>8H',u.mem_read(settings(t),16)));vals[1]&=0xff00;return tuple(vals)
prior=[norm(t) for t in range(6)]
stale=0x8000100c
for t in range(6):u.mem_write(stale+70+t*66,bytes(u.mem_read(raw(t)+76,10)))
target=rawproject+28+30710;u.reg_write(C.UC_M68K_REG_A2,target);u.emu_start(0x40055c5c,0x40055c62,count=5000000)
# Aucun appel de reset au cache natif : reproduire le chemin materiel.
r.call(a['lf2n_sync'],ctx,stale)
expected=(0x7000,0x400,0x4000,0x7f00,0,0,0,0x4000)
if v=='v214':
 assert all(norm(t)[0]==prior[t][0] and norm(t)[3]==prior[t][3] and norm(t)[7]==prior[t][7] for t in range(6))
 print('PASS reproduced v214: old native sound/frame overrides new-pattern LFO2 speed/destination/depth',flush=True)
else:
 assert [norm(t) for t in range(6)]==[expected]*6,[norm(t) for t in range(6)]
 for i in range(32):r.call(a['lf2n_sync'],ctx,stale)
 assert [norm(t) for t in range(6)]==[expected]*6
 print('PASS new pattern: all eight LFO2 controls default on six tracks despite32 stale native frames',flush=True)
 target=rawproject+28;u.reg_write(C.UC_M68K_REG_A2,target);u.emu_start(0x40055c5c,0x40055c62,count=5000000);r.call(a['lf2n_sync'],ctx,stale)
 assert [norm(t) for t in range(6)]==prior
 print('PASS original pattern restores every LFO2 value exactly',flush=True)
 # Un edit suivi immediatement d audio ne doit pas attendre le poll UI.
 assert r.call(a['lf2_edit'],ctx,3,3,14)==1;r.call(a['lf2n_sync'],ctx,stale);assert norm(3)[3]==0xe00
 print('PASS immediate UI edit survives native sync without any UI storage poll',flush=True)
 r.w32(rawproject+8,0x12345678);r.call(xs['xp_frame']);assert '/L2p_12345678.cfg' in f
 saved=f['/L2p_12345678.cfg'];assert saved[:4]==b'L2P1' and len(saved)==11152
 for at,size,guard in allocs:assert bytes(u.mem_read(guard,16))==b'\x5a'*16,(hex(at),size)
 print('PASS full LFO2 bank first-save file and every allocation boundary',flush=True)

if v!='v214':
 expected_saved=[norm(t) for t in range(6)];u.mem_write(xp['bss'],bytes(xp['end']-xp['bss']));u.mem_write(ctx+192,bytes(96));r.call(xs['xp_frame']);assert [norm(t) for t in range(6)]==expected_saved
 print('PASS cold LFO2 runtime restores all eight controls on six tracks from the full file alone',flush=True)
 # Migration de L2x sans modifier ce fichier, plus cinq reglages des kits natifs.
 import zlib
 legacy_rows=bytearray(4608)
 for pid in range(96):
  for t in range(6):struct.pack_into('>3H',legacy_rows,pid*48+t*6,0x4000,0,0)
 struct.pack_into('>3H',legacy_rows,2*48+5*6,0x2123,0x3456,0x400)
 for i in range(12):legacy_rows[2*48+36+i]=i%2
 legacy_file=struct.pack('>4I',0x4c325831,0x12345678,4608,zlib.crc32(legacy_rows))+legacy_rows
 f['/L2x_12345678.cfg']=legacy_file;f.pop('/L2p_12345678.cfg')
 canonical=rawproject+0x2d1812+2*7094+28+5*100
 u.mem_write(canonical+76,struct.pack('>5H',0x5500,0x6a2,0x400,0xe00,0x6600))
 u.mem_write(xp['bss'],bytes(xp['end']-xp['bss']));r.call(xs['xp_frame'])
 target=rawproject+28+2*30710;u.reg_write(C.UC_M68K_REG_A2,target);u.emu_start(0x40055c5c,0x40055c62,count=5000000);r.call(a['lf2n_sync'],ctx,stale)
 assert norm(5)==(0x5500,0x600,0x2123,0xe00,0x400,0x3456,0x400,0x6600),norm(5)
 assert f['/L2x_12345678.cfg']==legacy_file
 print('PASS migration retains old fade/phase/mode and reads existing per-pattern native kit controls; legacy file untouched',flush=True)
 # Vraie sauvegarde/lecture d un son : les cinq champs importes ne sont pas ignores.
 r.call(0x40061866,raw(5),0,0)
 for field,value in enumerate((23000,7,18000,14,5,21000,3,24576)):assert r.call(a['lf2_edit'],ctx,5,field,value)==1
 record=0x937f0000;assert r.call(0x4005afa0,record,raw(5))==1
 assert r.call(a['lf2_edit'],ctx,5,3,11)==1
 assert r.call(0x4005aecc,raw(5),record)==1
 r.call(a['lf2n_sync'],ctx,stale)
 assert norm(5)==(23000&0xff80,0x700,0x4000,0xe00,0x500,0,0,24576),norm(5)
 print('PASS native sound export/import restores its encoded LFO2 values rather than the previous full-bank values',flush=True)

 # La polarite ne doit pas etre reprise du cache sortant pendant le poll UI.
 def switch_to(pid):
  target=rawproject+28+30710*pid;u.reg_write(C.UC_M68K_REG_A2,target);u.emu_start(0x40055c5c,0x40055c62,count=5000000);r.call(a['lf2n_sync'],ctx,stale)
 r.call(s['lp_sound_set'],4,1,1);r.call(xs['xp_frame']);assert r.call(s['lp_sound_get'],4,1)==1
 switch_to(3)
 # Copie immediatement apres le switch, avant tout poll UI de publication.
 assert r.call(0x40014bd2,handle(4))==1
 assert r.call(0x40014c88,handle(1),1,1)==1
 assert norm(1)==expected,norm(1)
 r.call(xs['xp_frame']);assert r.call(s['lp_sound_get'],4,1)==0
 print('PASS new-pattern LFO2 polarity defaults Bi and immediate sound copy uses the incoming bank, not the outgoing cache',flush=True)
 switch_to(4);r.call(s['lp_sound_set'],0,1,1);r.call(a['lf2n_sync'],ctx,stale);r.call(xs['xp_frame']);assert r.call(s['lp_sound_get'],0,1)==1
 switch_to(3);r.call(xs['xp_frame']);assert r.call(s['lp_sound_get'],0,1)==0
 switch_to(4);r.call(xs['xp_frame']);assert r.call(s['lp_sound_get'],0,1)==1
 print('PASS immediate polarity edits and per-pattern LFO2 polarity restoration',flush=True)
 # Aucun E/S ni heap lors du sync audio.
 for pc in (0x400802e0,0x4007bc5e,0x4007bb0a,0x4007e2f6):bind(pc,lambda args:(_ for _ in ()).throw(AssertionError('file/heap in audio sync')))
 r.call(a['lf2n_sync'],ctx,stale)
 print('PASS full-bank audio sync performs no file or heap calls',flush=True)
