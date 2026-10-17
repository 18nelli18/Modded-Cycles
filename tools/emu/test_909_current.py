"""Note 108 : vrai boot/cache puis callbacks des six slots 909 contre le C hote.
Capture avant ah_noenv : calcul 909 exact et un seul passage Wizard par voix.
Peripheriques/cache physique non emules ; samples synthetiques locaux.
"""
import ctypes,json,pathlib,struct,subprocess,tempfile,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
from test_model_tg import engine
import mcengine as E
import emac
ROOT=HERE.parents[1]
def main():
 image,runtime,ts,ram=boot('build/909-current/all',with_sram=True);drum=next(t for t in ts if t['id']=='model909-wizard-acid');s={k:int(v,16) for k,v in drum['symbols'].items()};ws=next(t['symbols'] for t in ts if t['id']=='sample-wizard');ah=int(ws['ah_noenv'],16)
 data=json.loads((ROOT/'build/909-current/engine-data.js').read_text().split('=',1)[1].strip().rstrip(';'));code=next(p for p in data['engine']['append']['parts'] if p['dest']=='0x46709000');own=bytes.fromhex(code['hex']);codefile=ROOT/'build/909-current/emac-909.bin';codefile.write_bytes(own);hooks=emac.disasm(str(codefile),0x46709000,0x46709000,0x46709000+len(own))
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);src=ROOT/'tools/machines/model909_full'
  (p/'ref.c').write_text('''#include "t9.c"
static struct t9_voice host[6];
void sample(int i,const uint8_t*p,uint32_t n){samples[i].data=p;samples[i].len=n;}
void init(int i,int k,uint32_t seed){t9_init(host+i,k,seed);}
void update(int i,int note,int decay,int color,int shape,int sweep,int contour,int accent,int trig){struct t9_knobs k={note,decay,color,shape,sweep,contour,accent};t9_update(host+i,&k,trig);}
void render(int i,int32_t*out){t9_render(host+i,out);}
''')
  subprocess.run(['gcc','-shared','-fPIC','-O2','-fwrapv','-I'+str(src),str(p/'ref.c'),'-o',str(p/'ref.so')],check=True);ref=ctypes.CDLL(str(p/'ref.so'));ref.sample.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32];buffers=[]
  # Ces octets viennent du vrai firmware construit par les quatre uploads.
  for i in range(4):
   at,n=struct.unpack_from('>II',runtime,s['samples']-0x46700000+8*i);assert n>2;data=runtime[at-0x46700000:at-0x46700000+(n+1)//2];buf=ctypes.create_string_buffer(data);buffers.append(buf);ref.sample(i,buf,n)
  for variant in range(3):
   e=engine(image,end=E.BASE+len(image),payload=(0x46700000,runtime));e.uc.mem_write(0x80000000,ram);e.emac.install(hooks);captured={};calls={};shapes=[64,64,variant%2,variant%2,variant,variant%2]
   def capture(u,pc,size,data):
    sp=u.reg_read(mk.UC_M68K_REG_A7);out,v=struct.unpack('>II',bytes(u.mem_read(sp+4,8)));lane=(v-E.VOICE0)//E.VSTRIDE;captured[lane]=struct.unpack('>32i',u.mem_read(out,128));calls[lane]=calls.get(lane,0)+1
   e.uc.hook_add(UC_HOOK_CODE,capture,begin=ah,end=ah)
   for lane in range(6):
    e.set(lane,machine=lane,note=60,pitch=64,color=64,shape=shapes[lane],sweep=64,contour=64,punch=0,gate=0,finetune=64,decay=60);ref.init(lane,lane,(0x9090+E.VOICE0+E.VSTRIDE*lane)&0xffffffff)
   protected=bytes(e.uc.mem_read(0x46737000,0xb000));audible=[False]*6;after=[False]*6
   for block in range(24):
    trig=block in (0,8,16);captured.clear();calls.clear();e._write_params()
    for lane,pre in enumerate(['bd','sd','hh','rc','tom','cy']):
     v=E.VOICE0+lane*E.VSTRIDE;e.uc.reg_write(mk.UC_M68K_REG_A2,E.PARAMS+0xe+lane*0x42);e.uc.reg_write(mk.UC_M68K_REG_D2,lane);e.uc.mem_write(v+0x38,struct.pack('>I',int(trig)))
     e.call(s['t9_'+pre+'_update'],60<<16,v,E.PARAMS+0xe+lane*0x42)
     e.call(s['t9_'+pre+'_render'],E.TRACK_BASE+lane*128,v)
     after[lane]|=any(struct.unpack('>32i',e.uc.mem_read(E.TRACK_BASE+lane*128,128)))
    assert calls=={i:1 for i in range(6)},('etage Wizard double/manquant',variant,block,calls)
    for lane in range(6):
     ref.update(lane,60<<16,60,64,shapes[lane],64,64,0,int(trig));raw=(ctypes.c_int32*32)();ref.render(lane,raw);expected=tuple(max(-65535,min(65535,x))*32768 for x in raw)
     assert captured[lane]==expected,('DSP',variant,block,lane,captured[lane][:8],expected[:8])
     audible[lane]|=any(expected)
   assert bytes(e.uc.mem_read(0x46737000,0xb000))==protected,'tables Wizard/CHORD ecrasees'
   assert all(audible) and all(after),('silence',variant,audible,after);assert not e.unmapped
   print('PASS six slots 909 / C hote exact, types',variant,'24 blocs/retriggers, Wizard une seule fois',flush=True)
 print('LIMITES : callbacks notes explicites, pas de sequenceur audio complet ni CPU/I/O physiques ; combinaison experimentale')
if __name__=='__main__':main()
