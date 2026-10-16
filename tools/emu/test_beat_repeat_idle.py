"""Note 105 : combo sans division, historique et sortie identiques au principal.
Comparaison des vrais modules ColdFire, stereo, wrap et lanes desactivees.
"""
import argparse,json,pathlib,random,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
ROOT=pathlib.Path(__file__).resolve().parents[2]
ORIGIN=0x46a00000
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',required=True);a=p.parse_args()
 old=json.loads((ROOT/'docs/flasher/beat-repeat-data.js').read_text().split('window.MCBeatRepeat=',1)[1].strip().rstrip(';'))
 new=json.loads(pathlib.Path(a.data).read_text());stock=main_os_from_syx(str(ROOT/'firmware/model-cycles_OS1.13.syx'))
 rng=random.Random(105);totals=[0,0]
 for stereo in (False,True):
  rigs=[]
  for data in (old,new):
   r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
   u.mem_map(ORIGIN,0x10000);u.mem_map(0x80000000,0x200000)
   code=bytearray.fromhex(data['hex'])
   for off in data['reloc']:struct.pack_into('>I',code,off,struct.unpack_from('>I',code,off)[0]+ORIGIN)
   u.mem_write(ORIGIN,bytes(code));r.s={k:ORIGIN+v for k,v in data['symbols'].items()}
   r.count=0
   def count(u,pc,size,user,r=r):r.count+=1
   u.hook_add(UC_HOOK_CODE,count,begin=ORIGIN,end=ORIGIN+len(code))
   for name,value in [('br_history',0x41000000),('br_keys',3),('br_requested',-1),('br_blocks',4094),('br_side',0x80010000 if stereo else 0),('br_side_on',0x80011000 if stereo else 0)]:r.w32(r.s[name],value&0xffffffff)
   r.w32(0x40a7883c,1);r.w32(0x40a78840,1)
   rigs.append(r)
  for block in range(8):
   samples=[rng.choice([-2147483648,2147483647,rng.randint(-2147483648,2147483647),0]) for _ in range(12*32)]
   for index,r in enumerate(rigs):
    for track in range(12):
     base=0x80001858 if track<6 else 0x80010000
     r.u.mem_write(base+(track%6)*128,struct.pack('>32i',*samples[track*32:(track+1)*32]))
    for lane in range(6):r.w32(0x80011000+lane*4,int((lane+block)%3!=0))
    r.u.mem_write(STACK,struct.pack('>I',STOP));r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
    r.count=0;r.u.emu_start(r.s['br_audio'],STOP,count=1000000)
    assert r.u.reg_read(mk.UC_M68K_REG_PC)==STOP
    assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
    totals[index]+=r.count
   for base,length in [(0x41000000,12*131072*2),(0x80001858,6*128),(0x80010000,6*128)]:
    assert bytes(rigs[0].u.mem_read(base,length))==bytes(rigs[1].u.mem_read(base,length)),(stereo,block,hex(base))
   for name in ('br_wet','br_valid','br_active','br_blocks','br_start','br_length'):
    assert rigs[0].r32(rigs[0].s[name])==rigs[1].r32(rigs[1].s[name]),name
  print('PASS combo seul : audio/historique/etats identiques, stereo',stereo,flush=True)
 assert totals[1]<totals[0];print('PASS instructions combo seul',totals,'reduction',round(100*(1-totals[1]/totals[0]),1),'%; pas cycles materiels',flush=True)
if __name__=='__main__':main()
