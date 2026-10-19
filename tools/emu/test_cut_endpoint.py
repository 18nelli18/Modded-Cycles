"""Note136 : vrai fondu entier, dernier sample nul, gains continus entre blocs."""
import pathlib,sys,json,struct,random,argparse
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from midi_safety_load import load
from unicorn import m68k_const as mk
ROOT=HERE.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',default='usb');p.add_argument('--case');a=p.parse_args();case=a.case or 'build/cut-endpoint/'+a.profile;r,gov=load(case);meta=json.loads((ROOT/(case+'.json')).read_text());sy={k:int(v,16) for t in meta['tweaks'] for k,v in t.get('symbols',{}).items()};rng=random.Random(136);buf=0x93010000
 for flen in (2,8):
  step=65536//(32*flen-1)
  for remaining in range(flen,0,-1):
   for trial in range(64):
    data=[rng.choice((-2147483648,2147483647,0,rng.randrange(-2147483648,2147483648))) for _ in range(32)];r.u.mem_write(buf,struct.pack('>32i',*data));r.u.reg_write(mk.UC_M68K_REG_A2,buf);r.u.reg_write(mk.UC_M68K_REG_D1,65536//(32*flen));r.u.reg_write(mk.UC_M68K_REG_D4,remaining*32*(65536//(32*flen)));r.u.reg_write(mk.UC_M68K_REG_D3,31);r.u.reg_write(mk.UC_M68K_REG_D2,0x12345678)
    r.call(sy['cf_fade']);got=struct.unpack('>32i',r.u.mem_read(buf,128));expected=tuple(x*((remaining*32-1-i)*step)//65536 for i,x in enumerate(data))
    assert got==expected,(flen,remaining,trial)
    assert r.u.reg_read(mk.UC_M68K_REG_D2)==0x12345678
    if remaining==1:assert got[-1]==0
 # Appel reel de voice_after : la boucle en SRAM doit atteindre le helper.
 for flen in (2,8):
  r.u.mem_write(buf,struct.pack('>32i',*([0x40000000]*32)));r.u.mem_write(gov['gov_fading'],bytes([1,0,0,0,0,0]));r.u.mem_write(gov['gov_flen'],bytes([flen,0,0,0,0,0]));r.u.mem_write(gov['gov_free'],bytes(6));r.u.mem_write(gov['gov_stolen'],bytes(6));r.w32(0xfc07000c,1000);r.call(gov['voice_after'],0,buf)
  expected=tuple(0x40000000*((31-i)*(65536//(32*flen-1)))//65536 for i in range(32));assert struct.unpack('>32i',r.u.mem_read(buf,128))==expected
  assert bytes(r.u.mem_read(gov['gov_fading'],1))==bytes([0]) and bytes(r.u.mem_read(gov['gov_stolen'],1))==bytes([1])
 data=struct.pack('>32i',*([12345678]*32));r.u.mem_write(buf,data);r.u.mem_write(gov['gov_fading'],bytes(6));r.call(gov['voice_after'],0,buf);assert bytes(r.u.mem_read(buf,128))==data
 print('PASS',a.profile,':640 blocs extremes/aleatoires, fondu Q16 exact, fin zero, registre preserve ; deux durees natives')
if __name__=='__main__':main()
