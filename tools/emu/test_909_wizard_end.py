"""909 : vrais lookups/borne/edition End, RC Type et DSP strictement conserves.

Boot et constructeur OS reels. Le son/handle fourni correspond aux classes
natives ; seuls selection, observateurs et touches UI sont instrumentes.
"""
import argparse,pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
import test_sdvintage_7th as T
from unicorn import m68k_const as mk,UC_HOOK_CODE
BASE=0x40000400

def prepare(case):
 img,mem,ts=boot_case(case);wizard=next(t for t in ts if t['id']=='sample-wizard');sy={k:int(v,16) for k,v in wizard['symbols'].items()}
 r=T.UI(img);r.uc.mem_write(BASE,img);r.uc.mem_map(0x46700000,0x400000);r.uc.mem_map(0x80000000,0x20000)
 for at,raw in mem:r.uc.mem_write(at,raw)
 r.uc.reg_write(mk.UC_M68K_REG_SR,0x2000);r.call(0x4005a274)
 # Construire seulement la partie descripteurs du vrai pre audio Wizard.
 # Le gabarit de page Chord est fourni ; ses six IDs sont remplaces par Wizard.
 r.uc.mem_write(0x40a71708,struct.pack('>19I',1,*([0]*18)))
 r.uc.reg_write(mk.UC_M68K_REG_A6,0x93008000);r.uc.reg_write(mk.UC_M68K_REG_D1,0)
 r.uc.reg_write(mk.UC_M68K_REG_A7,0x93007000)
 r.uc.emu_start(sy['sm_sampler_pre_full'],sy['dsc_skip'],count=50000)
 assert r.uc.reg_read(mk.UC_M68K_REG_PC)==sy['dsc_skip']
 return r,img,mem,ts,sy

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',default='build/909-preview/all');p.add_argument('--after',default='build/909-wizard-end/all');a=p.parse_args();before=prepare(a.before);after=prepare(a.after)
 for state,expected in ((before,62),(after,52)):
  r,img,mem,ts,sy=state
  assert r.call(0x4005a692,12,6)==expected
  assert r.u32(sy['sampler_descr']+20)==expected
  r.call(0x4005a65a,expected);lo,hi,default=struct.unpack('>3i',r.uc.mem_read(T.SCRATCH,12))
  assert lo==0 and hi==(256 if expected==62 else 32512),(expected,lo,hi)
 print('PASS reproduction : End909 avant0..1 ; apres0..127 via vrai lookup et vrai descripteur prive Wizard')
 # Le descripteur RC Type reste EXACTEMENT pareil, pas uniquement sa borne.
 rb,ra=before[0],after[0];tb=rb.u32(0x4005a4f4);ta=ra.u32(0x4005a4f4)
 assert bytes(rb.uc.mem_read(tb,81*56))==bytes(ra.uc.mem_read(ta,81*56))
 ra.call(0x4005a65a,62);assert struct.unpack('>3i',ra.uc.mem_read(T.SCRATCH,12))[:2]==(0,256)
 print('PASS tous81descripteurs909 identiques ; RC Type conserve0/1, aucun elargissement global')
 # Le vrai fine_hook reconnait le nouvel ID tout en laissant le meme slot12.
 values=[]
 for state,desc in ((before,62),(after,52)):
  r,img,mem,ts,sy=state;handle=0x93010000;object_=0x93010100;vt=0x93010200;raw=0x93010300;getter=0x93010400
  r.uc.mem_write(handle,struct.pack('>II',0x400fd134,object_));r.uc.mem_write(object_,struct.pack('>II',vt,raw))
  r.uc.mem_write(vt+40,struct.pack('>I',getter));r.uc.mem_write(getter,bytes.fromhex('206f0004202800044e75'));r.uc.mem_write(raw+38,b'\6')
  values.append([r.call(sy['fine_hook'],handle,desc,10000,delta) for delta in (-2048,-512,-256,0,256,512,2048)])
 assert values[0]==[256]*7,values
 assert values[1]==[7952,9872,9968,10000,10032,10128,12048],values
 print('PASS edition fine native conservee pour End, pas de perte des fractions ou changement du slot sauvegarde')
 # Le dessin et le formatter decimals suivent le nouvel ID ; RC Type intact.
 r=after[0];sy=after[4];rc=bytes(r.uc.mem_read(0x40a71754+62*100,100))
 r.uc.reg_write(mk.UC_M68K_REG_D1,1);r.call(sy['apply_names'])
 assert r.u32(0x40a71754+52*100+32)==0x4004a440
 assert r.u32(0x40a71754+52*100+48)==sy['fine_draw']
 assert bytes(r.uc.mem_read(0x40a71754+62*100,100))==rc
 r.uc.reg_write(mk.UC_M68K_REG_D1,0);r.call(sy['apply_names'])
 assert r.u32(0x40a71754+52*100+32)==0x400456c8
 assert r.u32(0x40a71754+52*100+44)==0
 print('PASS vrai formatter/dessin decimaux installe puis restaure sur End ; record RC Type jamais modifie')
 # Les corps des six voix audio909 sont exactement les memes octets.
 for name,at in next(t for t in before[3] if t['id']=='model909-wizard-acid')['symbols'].items():
  if name.startswith('t9_') and name.endswith(('_update','_render')):
   address=int(at,16)
   def data(state):
    for base,raw in state[2]:
     if base<=address<base+len(raw):return raw[address-base:address-base+64]
    raise AssertionError(name)
   assert data(before)==data(after),name
 assert any('br_load_address' in t.get('symbols',{}) for t in after[3])
 print('PASS corps DSP909 conserves ; diagnostic seulement dans le test')
 print('LIMITES : manipulation physique des marqueurs Slice et ecoute a confirmer sur appareil')
if __name__=='__main__':main()
