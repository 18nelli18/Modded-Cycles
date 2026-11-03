"""Route HALL reelle : PCM et etat identiques a350, delai/gates inchanges."""
from pathlib import Path
import argparse,json,random,struct,sys
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from restore_hall362 import apply
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
m=json.loads((a.build/'BUILD.json').read_text());native=(a.capture/'native.bin').read_bytes();old=(a.capture/'runtime.bin').read_bytes();new=bytearray(old);d=apply(m,new,a.reference);reference=(a.reference/'runtime.bin').read_bytes();fs=m['fx_menu']['symbols'];rigs=[]
for image in [reference,bytes(new)]:
 r=Rig(native,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(0x46700000,0x300000);r.u.mem_write(0x46700000,image);rigs.append(r)
IN=0x93180000;OUT=IN+512;PARAM=IN+1024;rng=random.Random(362);nonzero=0
for block in range(512):
 values=[rng.randrange(-1000000000,1000000001) for _ in range(64)] if block<160 else [0]*64;results=[]
 for r in rigs:
  r.u.mem_write(IN,struct.pack('>64i',*values));r.u.mem_write(PARAM,struct.pack('>2h',90<<8,64<<8));r.u.mem_write(OUT-4,b'ABCD');r.u.mem_write(OUT+256,b'EFGH');r.call(fs['fx_hall'],OUT,IN,PARAM)
  assert bytes(r.u.mem_read(OUT-4,4))==b'ABCD' and bytes(r.u.mem_read(OUT+256,4))==b'EFGH';assert bytes(r.u.mem_read(IN,256))==struct.pack('>64i',*values)
  results.append(bytes(r.u.mem_read(OUT,256)))
 assert results[0]==results[1],block;nonzero+=any(results[1])
assert nonzero>300,nonzero
eco=m['eco_fx351'];at=eco['code']-0x46700000;assert new[at:at+eco['code_bytes']]==old[at:at+eco['code_bytes']]
a.output.write_text(json.dumps(dict(module=d,blocks=512,PCM_matches350=True,nonzero_blocks=nonzero,real_HALL_entry=True,delay_gate_code_unchanged=True,buffer_guards=True),indent=2)+'\n');print('PASS512 real HALL calls: exact350 PCM, audible tail, buffer guards, delay/gates unchanged')
