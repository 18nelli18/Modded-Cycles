"""WAVE115 : demarrage reel, rendu natif, remplacement par fichier natif simule.
Aucun MIDI physique, aucun resultat CPU extrapole a la machine.
"""
from pathlib import Path
import sys,json,struct,hashlib
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
import test_wizard_playback,emac,numpy as np
from test_wizard_playback import fixtures
from boot_candidate import boot,load
from unicorn import UC_HOOK_CODE,m68k_const as C
from mcengine import VOICE0,VSTRIDE,PARAMS,STOP,STACK
version=sys.argv[1] if len(sys.argv)>1 else 'v115'
stem='staging/all-features-polivoks-cpu-trim-test-'+version
m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());a=m['wave_starter'];DATA=a['data'];BASE=0x4677b2b8;COUNT=0x4677b2a0
pcm=(R/'output/firmware'/('governor-recovery-'+version)/'wave-starter.pcm').read_bytes()
assert hashlib.sha256(pcm).hexdigest()==a['pcm_sha256']
im,mem=boot(R/'output/firmware'/(stem+'.syx'))
assert mem[0][1][DATA-mem[0][0]:DATA-mem[0][0]+len(pcm)]==pcm
print('PASS native boot preserves all 16 starter frames and their exact converted PCM',flush=True)
baseline='v111adult' if version.endswith('adult') else 'v111'
_,oldmem=boot(R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+baseline+'.syx'))
table=m['tiny_extra']['data'];nm=m['tiny_extra']['machine_count'];row=table+4*(nm+14)
allowed=[(a['code'],a['code']+a['code_bytes']),(DATA,DATA+len(pcm)),(0x4677a750,0x4677a758),(0x4677a684,0x4677a68a),(0x46779000,0x46779008),(0x4677b2a0,0x4677b2d0)]
for i,(x,y) in enumerate(zip(oldmem[0][1],mem[0][1])):
 if x!=y:assert any(lo<=mem[0][0]+i<hi for lo,hi in allowed),('unexpected runtime change',hex(mem[0][0]+i),x,y)
assert len(oldmem[0][1])==len(mem[0][1])
assert m['tiny_extra']['menu_order'][-2:]==[22,17]
print('PASS runtime changes confined to WAVE starter, preloaded state and native-entry hooks; other machines/FX preserved',flush=True)
if '--static' in sys.argv:sys.exit(0)
def make(v):
 e=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-'+v],native_chordkeys=True,audit_count=False)[0]
 e.uc.mem_map(0x46900000,0x1200000)
 path=R/'output/firmware'/('native-wave-'+v+'.bin');path.write_bytes(e.uc.mem_read(0x46779000,0x1500));e.emac.install(emac.disasm(str(path),0x46779000,0x46779000,0x4677a500))
 for lane in range(6):e.set(lane,machine=14,note=36+lane*7,pitch=64,color=lane*25,shape=0,sweep=127,contour=0,finetune=64,decay=110,gate=0)
 return e
e=make(version);reference=make('v111')
def rd(engine,at):return int.from_bytes(engine.uc.mem_read(at,4),'big')
def wr(engine,at,val):engine.uc.mem_write(at,struct.pack('>I',val&0xffffffff))
assert all(rd(e,BASE+4*l)==DATA and rd(e,COUNT+4*l)==68608 for l in range(6))
assert not np.any(reference.block(63))
for lane in range(6):
 reference.uc.mem_write(DATA,pcm);wr(reference,BASE+4*lane,DATA);wr(reference,COUNT+4*lane,68608)
# Reinitialiser la reference : la premiere note silencieuse a avance son enveloppe.
reference=make('v111');reference.uc.mem_write(DATA,pcm)
for lane in range(6):wr(reference,BASE+4*lane,DATA);wr(reference,COUNT+4*lane,68608)
peaks=np.zeros(6,dtype=np.int64)
for b in range(10):
 out=e.block(63 if b==0 else 0);ref=reference.block(63 if b==0 else 0)
 assert np.array_equal(out,ref),('native PCM changed',b)
 peaks=np.maximum(peaks,np.max(np.abs(out),axis=1))
assert np.all(peaks>10000),peaks
assert all(rd(e,BASE+4*l)==DATA and rd(e,COUNT+4*l)==68608 for l in range(6))
assert bytes(e.uc.mem_read(DATA,len(pcm)))==pcm
assert not e.unmapped and not reference.unmapped
print('PASS six WAVE tracks audible without files; native output exactly equals v111 with the same manually loaded table; shared PCM unchanged',peaks.tolist(),flush=True)
assert rd(e,0x4677a686)==0x46900000
# Les API fichier seules sont simulees ; le parseur chargeur WT_LOAD reste natif.
custom=struct.pack('>I',0x57544231)+struct.pack('>I',len(pcm))+bytes(56)+np.negative(np.frombuffer(pcm,dtype='>i2').astype(np.int32)).clip(-32768,32767).astype('>i2').tobytes()
state={'offset':0,'open':0,'read':0,'close':0,'fail':False}
def file_api(u,pc,size,data):
 sp=u.reg_read(C.UC_M68K_REG_A7);args=struct.unpack('>4I',bytes(u.mem_read(sp,16)));result=0
 if pc==0x4007e4f4:state['open']+=1;state['offset']=0;result=-1 if state['fail'] else 0
 elif pc==0x4007baaa:
  state['read']+=1;dest,n=args[1:3];chunk=custom[state['offset']:state['offset']+n];u.mem_write(dest,chunk);state['offset']+=len(chunk);result=len(chunk)
 else:state['close']+=1
 u.reg_write(C.UC_M68K_REG_D0,result&0xffffffff);u.reg_write(C.UC_M68K_REG_A7,sp+4);u.reg_write(C.UC_M68K_REG_PC,args[0])
for pc in [0x4007e4f4,0x4007baaa,0x4007bc1c]:e.uc.hook_add(UC_HOOK_CODE,file_api,begin=pc,end=pc)
lane=2;handle=0x4677ab72+16*lane;e.uc.mem_write(handle,struct.pack('>4I',1,0,len(custom),0))
e.uc.reg_write(C.UC_M68K_REG_D0,lane);assert e.call(0x4677a620)==0
custom_base=rd(e,BASE+4*lane);assert custom_base!=DATA and rd(e,COUNT+4*lane)==68608
assert bytes(e.uc.mem_read(custom_base,len(pcm)))==custom[64:]
e.block(63);assert rd(e,BASE+4*lane)==custom_base
assert bytes(e.uc.mem_read(DATA,len(pcm)))==pcm
assert all(rd(e,BASE+4*l)==DATA for l in range(6) if l!=lane)
print('PASS native file import replaces only the selected track and survives subsequent updates; starter table and other tracks untouched',state,flush=True)
# Echec du fichier : prochain bloc retablit le fallback et joue encore.
state['fail']=True;e.uc.reg_write(C.UC_M68K_REG_D0,lane);assert e.call(0x4677a620)==2
assert rd(e,BASE+4*lane)==0;e.block(63);assert rd(e,BASE+4*lane)==DATA
print('PASS failed file open recovers the starter on the next audio update',flush=True)
# Pad : le chargeur reste accessible depuis le fallback ; aucun registre perdu.
sounds=0x42410000;wr(e,0x40a78888,sounds)
for l in range(6):e.uc.mem_write(sounds+28+100*l+38,bytes([14]))
def ui_stub(u,pc,size,data):
 sp=u.reg_read(C.UC_M68K_REG_A7);u.reg_write(C.UC_M68K_REG_PC,rd(e,sp));u.reg_write(C.UC_M68K_REG_A7,sp+4)
e.uc.hook_add(UC_HOOK_CODE,ui_stub,begin=0x4677a8ac,end=0x4677a8ac)
e.uc.hook_add(UC_HOOK_CODE,lambda u,pc,size,data:u.emu_stop(),begin=0x40081724,end=0x40081724)
state['fail']=False
registers=[getattr(C,'UC_M68K_REG_D'+str(i)) for i in range(1,8)]+[getattr(C,'UC_M68K_REG_A'+str(i)) for i in range(6)]
expected={reg:0x11000100+i*0x100 for i,reg in enumerate(registers)}
for reg,val in expected.items():e.uc.reg_write(reg,val)
e.uc.reg_write(C.UC_M68K_REG_A6,0x90008000);opened=state['open'];e.call(0x4677a750,lane)
assert e.uc.reg_read(C.UC_M68K_REG_PC)==0x40081724
assert e.uc.reg_read(C.UC_M68K_REG_D0)==127
assert all(e.uc.reg_read(reg)==val for reg,val in expected.items())
assert e.uc.reg_read(C.UC_M68K_REG_A7)==STACK-0x200-108
assert e.uc.reg_read(C.UC_M68K_REG_A6)==STACK-0x200-4
assert rd(e,STACK-0x200-4)==0x90008000
assert state['open']==opened+1 and rd(e,BASE+4*lane)!=DATA
opened=state['open'];e.call(0x4677a750,lane);assert state['open']==opened
print('PASS first-pad custom loading from factory fallback; subsequent pads retain loaded table; native register/stack continuation preserved',flush=True)
# Tous les fichiers sont charges dans les six fenetres distinctes, hors FX/code.
ranges=[(m['fx_menu']['code'],m['fx_menu']['code_bytes']),(a['code'],a['code_bytes']),(m['legacy']['code'],m['legacy']['code_bytes']),(DATA,len(pcm))]
before=[bytes(e.uc.mem_read(at,n)) for at,n in ranges]
for l in range(6):
 e.uc.mem_write(0x4677ab72+16*l,struct.pack('>4I',1,0,len(custom),0));e.uc.reg_write(C.UC_M68K_REG_D0,l);assert e.call(0x4677a620)==0
 assert rd(e,BASE+4*l)==0x46900040+0x300000*l
 assert bytes(e.uc.mem_read(rd(e,BASE+4*l),len(pcm)))==custom[64:]
assert before==[bytes(e.uc.mem_read(at,n)) for at,n in ranges]
assert not e.unmapped
print('PASS six custom WAVE buffers disjoint and beyond runtime; FX, LEGACY, fallback code and starter PCM intact',flush=True)
for machine,handle0 in [(14,0),(13,1)]:
 wr(e,BASE,DATA);wr(e,COUNT,68608);wr(e,0x4677ab72,handle0);e.uc.mem_write(sounds+28+38,bytes([machine]));opened=state['open']
 e.call(0x4677a750,0)
 assert state['open']==opened and rd(e,BASE)==DATA and rd(e,COUNT)==68608
assert not e.unmapped
print('PASS pads with no selected file and pads on other machines retain their original behavior',flush=True)

# Ancien pointeur update natif, sans passer par la nouvelle table de dispatch.
for lane in range(6):
 wr(e,BASE+4*lane,0);wr(e,COUNT+4*lane,0);e.uc.mem_write(VOICE0+VSTRIDE*lane+0x38,struct.pack('>I',1))
e._write_params()
for lane in range(6):
 e.call(0x46779000,(36+lane*7)<<16,VOICE0+VSTRIDE*lane,PARAMS+14+66*lane)
 assert rd(e,BASE+4*lane)==DATA and rd(e,COUNT+4*lane)==68608
 assert rd(e,0x4677b000+112*lane+28)==16
print('PASS original/cached WAVE update entry restores the starter on all six lanes',flush=True)
