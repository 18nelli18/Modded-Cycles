"""Compiler des lignes et exercer les repetitions dans le sequenceur natif."""
from pathlib import Path
import subprocess,os,json,struct
HERE=Path(__file__).resolve().parent
# Reutiliser le banc ISR natif sans executer ses cas Direct Jump.
source=(HERE/'test_direct_jump.py').read_text().split('\ndef steps(')[0]
exec(compile(source,str(HERE/'test_direct_jump.py'),'exec'))
W=a.output.parent;W.mkdir(parents=True,exist_ok=True);cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*args):return subprocess.check_output([cross+t+'.exe',*map(str,args)],text=True)
CODE=0x46936000
run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-c',R/'tools/machines/song/song.c','-o',W/'song.o')
run('ld','-Ttext',hex(CODE),'-e','song_compile','-o',W/'song.elf',W/'song.o');run('objcopy','-O','binary',W/'song.elf',W/'song.bin')
symbols={v[2]:int(v[0],16) for line in run('nm',W/'song.elf').splitlines() if len(v:=line.split())==3}
s=Seq(IMG);e=s.e;e.u.mem_write(CODE,(W/'song.bin').read_bytes());record=0x4f041000;mapping=record+512
def compile(rows):
 e.u.mem_write(record,struct.pack('>II',len(rows),1)+b''.join(bytes(row) for row in rows));return e.call(symbols['song_compile'],record,CH,mapping,PAT0,KIT0)[0]
rows=[(0,2,0,0),(1,1,1,0),(0,3,0,0)]
assert compile(rows)==6
assert list(e.u.mem_read(mapping,6))==[0,0,1,2,2,2]
for i,pat in enumerate([0,0,1,0,0,0]):assert e.r32(CH+8*i)==s.pat(pat) and e.r32(CH+8*i+4)==s.kit(pat)
before=bytes(e.u.mem_read(CH,512))
for bad in [[],[(96,1,0,0)],[(0,0,0,0)],[(0,65,0,0)],[(0,1,64,0)],[(0,1,0,1)],[(0,40,0,0),(1,40,0,0)]]:
 assert compile(bad)==0 and bytes(e.u.mem_read(CH,512))==before
assert compile([(0,64,0,0)])==64
compile(rows)
for i in (0,1):s.setpat(i,length=4)
e.call(0x40055cd6,CH,6);e.w32(0x4230877c,1);e.call(0x400542dc)
seen=[];last=None
for tick in range(2600):
 s.isr();index=e.r32(0x40a78634)
 if index!=last:seen.append(index);last=index
 if len(seen)>=8:break
assert seen[:7]==[0,1,2,3,4,5,0],seen
a.output.write_text(json.dumps(dict(native_chain_indices=seen,repeated_same_pattern_advances=True,invalid_rows_do_not_change_output=True,capacity=64,hardware_tested=False),indent=2)+'\n')
print('PASS song rows compiled and native chain repeats/wrap',seen,flush=True)
