"""LEGACY prive : MSFA Apache de Dexed, SysEx Yamaha et art original.
Les cartouches de l utilisateur restent seulement dans le dossier de build.
"""
from pathlib import Path
import subprocess,os,json,struct,hashlib
CODE=0x46850000;ART=0x46888000;BSS=0x46890000;END=0x468b0000

def unpack(p):
 out=[]
 for k in range(6):
  q=p[k*17:k*17+17];out+=list(q[:11])+[q[11]&3,(q[11]>>2)&3,q[12]&7,q[13]&3,(q[13]>>2)&7,q[14],q[15]&1,(q[15]>>1)&31,q[16],(q[12]>>3)&15]
 out+=list(p[102:110])+[p[110],p[111]&7,(p[111]>>3)&1]+list(p[112:116])+[p[116]&1,(p[116]>>1)&7,(p[116]>>4)&7,p[117]]+list(p[118:128])+[63]
 assert len(out)==156
 return out

def bank(path):
 raw=Path(path).read_bytes();assert len(raw)==4104 and raw[:2]==bytes([240,67]) and raw[2]<16 and raw[3:6]==bytes([9,32,0]) and raw[-1]==247
 assert not any(x>127 for x in raw[6:-1]) and sum(raw[6:-1])&127==0,'Checksum cartouche DX7 invalide'
 # Premiers slots demandes par AveyCole ; le reste garde l ordre source.
 order=[0,2,15]+[i for i in range(32) if i not in (0,2,15)]
 voices=[unpack(raw[6+128*i:6+128*(i+1)]) for i in order]
 return voices,dict(file=Path(path).name,sha256=hashlib.sha256(raw).hexdigest(),private_only=True,source_slots=order,names=[bytes(v[145:155]).decode('ascii').strip() for v in voices])

def icon():
 p=[[0]*34 for _ in range(34)]
 for y in [4,13,22]:
  for x in [5,20]:
   for yy in range(y,y+7):
    for xx in range(x,x+9):
     if yy in [y,y+6] or xx in [x,x+8]:p[yy][xx]=1
 for y in range(11,22):p[y][9]=p[y][24]=1
 for x in range(9,25):p[31][x]=1
 for y in range(29,32):p[y][9]=p[y][24]=1
 from build_machine_identity_test import encode
 return encode(p)

def prepare(root,build,previous_popup,notice,bank_path,reference=False,classics_path=None,optimize=False,bank_safe=False,bank_guard=False,bank_chunks=False,bank_queue=False,legacy_fast=False,legacy_deep=False,legacy_routing=False):
 root=root.resolve();build=build.resolve();src=root/'tools/machines/dx7';voices,bm=bank(bank_path)
 if classics_path:
  raw=Path(classics_path).read_bytes();assert len(raw)==4104 and raw[:2]==bytes([240,67]) and raw[2]<16 and raw[3:6]==bytes([9,32,0]) and raw[-1]==247 and not any(x>127 for x in raw[6:-1]) and sum(raw[6:-1])&127==0
  replacements={'Hagedisk':7,'LowCarpopa':10,'SpaceProph':14,'VectorFron':0,'SIDpwm':21,'RainyHills':19,'Innsmouth':3,'FernLand':16};done=[]
  for i,name in enumerate(bm['names']):
   if name in replacements:
    slot=replacements[name];voices[i]=unpack(raw[6+128*slot:6+128*(slot+1)]);done.append(dict(slot=i,old=name,new=bytes(voices[i][145:155]).decode('ascii').strip(),source_slot=slot))
  assert len(done)==8;bm.update(classics_file=Path(classics_path).name,classics_sha256=hashlib.sha256(raw).hexdigest(),replacements=done,names=[bytes(v[145:155]).decode('ascii').strip() for v in voices])
 generated=build/'dx7_default.cc';generated.write_text('#include <stdint.h>\nextern "C" const uint8_t dx7_default_bank[32][156]='+str(voices).replace('[','{').replace(']','}')+';\n')
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH'];objs=[]
 files=[src/'core'/n for n in ['fm_core.cc','fm_op_kernel.cc','env.cc','pitchenv.cc','lfo.cc','freqlut.cc','tables.cc']]+[src/n for n in ['port.cc','bank.c','bridge.c','wrap.S','hooks.S']]+([src/'library.c'] if optimize else [])+([src/'kernels152.S'] if legacy_fast else [])+[generated]
 for f in files:
  obj=build/('dx7_'+f.name+'.o');objs.append(obj)
  args=[*(['-DDX7_BANK_GUARD=1'] if bank_guard else []),*(['-DDX7_BANK_CHUNKS=1'] if bank_chunks else [])+(['-DDX7_BANK_QUEUE=1'] if bank_queue else []),*(['-DDX7_BANK_SAFE=1'] if bank_safe else []),*(['-DDX7_OPT=1'] if optimize else []),'-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fwrapv','-Wall','-Wextra','-Wno-misleading-indentation']
  if legacy_fast:args+=['-DDX7_LEGACY_FAST=1']
  if legacy_routing:args+=['-DDX7_ROUTING154=1']
  if legacy_deep and f.name in ('port.cc','fm_core.cc','env.cc','pitchenv.cc','lfo.cc'):args+=['-O3','-funroll-loops','-DDX7_LEGACY_DEEP=1']
  cxx=f.suffix=='.cc'
  if cxx:args+=['-fno-exceptions','-fno-rtti','-fno-threadsafe-statics','-fno-use-cxa-atexit']
  if reference:args+=['-DDX7_REFERENCE=1']
  subprocess.run([cross+('g++.exe' if cxx else 'gcc.exe'),*args,'-c',str(f),'-o',str(obj)],check=True)
 libgcc=subprocess.check_output([cross+'gcc.exe','-mcpu=54418','-print-libgcc-file-name'],text=True).strip()
 ld=build/'dx7.ld';elf=build/'dx7.elf';binary=build/'dx7.bin'
 chunk_base = 0x468a8000 if bank_queue else 0x46880000
 chunk_section = f'.bankchunks {chunk_base:#x} (NOLOAD) : {{ *(.bankchunks) }} dx7_chunks_end = .;' if bank_chunks else ''
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} . = ALIGN(4); dx7_code_end = .; {chunk_section} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); dx7_end = .; /DISCARD/ : {{ *(.eh_frame*) *(.init_array*) *(.fini_array*) }} }}\ndx7_previous_popup = {previous_popup:#x};\ndx7_notice = {notice:#x};\n')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objs),libgcc],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 assert sy['dx7_code_end'] <= (0x46880000 if bank_chunks else ART) and sy['dx7_end']<END
 if bank_chunks: assert chunk_base < sy['dx7_chunks_end'] < (0x468ae000 if bank_queue else ART)
 profile=dict(machine=21,name='LEGACY',icon='six-operators',**{'class':'SYNTH'},style='DXFM',str=4,dex=5,mag=5)
 from build_machine_identity_test import stats,encode
 blob=bytearray(binary.read_bytes().ljust(sy['dx7_end']-CODE,b'\0'));pos=ART+56
 for desc,pixels,w,h in [(ART,stats(profile),48,33),(ART+28,icon(),34,34)]:
  mask=encode([[1]*w for _ in range(h)]);ptr=pos;blob[pos-CODE:pos-CODE+len(pixels)]=pixels;pos+=len(pixels);mp=pos;blob[pos-CODE:pos-CODE+len(mask)]=mask;pos+=len(mask);blob[desc-CODE:desc-CODE+28]=struct.pack('>7I',0x401117c8,w,h,2,ptr,mp,0)
 assert pos<BSS
 return bytes(blob),dict(name='LEGACY',machine=21,code=CODE,bss=BSS,end=sy['dx7_end'],code_bytes=binary.stat().st_size,symbols=sy,profile=profile,stats_descriptor=ART,icon_descriptor=ART+28,bank=bm,engine='Dexed MSFA Apache-2.0',source_revision='fea2f0f0f2c397799f59b27eb11c038cd34b22c5',controls=['Velocity','Voice','Brightness','EG Time'],voices_per_track=1,status='experimental',hardware_tested=False,reference=reference,sha256=hashlib.sha256(blob).hexdigest())
