"""Construction du moteur original inspire de Junior (Fors), note140.
Code separe des autres machines ; sources et tables mathematiques uniquement.
"""
import math,json,subprocess,os
from pathlib import Path
CODE=0x467e8000
BSS=0x467f0000

def tables():
 waves=[]
 for w in range(16):
  v=[]
  for i in range(32):
   t=i/32;sn=math.sin(2*math.pi*t)
   x=[sn,1-4*abs(t-.5),2*t-1,1 if i<16 else -1,
      1 if i<8 else -1,1 if i<4 else -1,
      (sn+math.sin(4*math.pi*t)*.5)/1.5,
      (sn+math.sin(6*math.pi*t)*.6)/1.6,
      math.sin(2*math.pi*(t+.15*sn)),
      (sn+math.sin(10*math.pi*t)*.5)/1.5,
      (math.sin(4*math.pi*t)+math.sin(6*math.pi*t))*.5,
      abs(sn)*2-1,(2*t-1)*(1 if i&4 else -1),
      ((i*13+7)%32)/15.5-1,
      (sn+math.sin(14*math.pi*t)*.4)/1.4,
      (1-4*abs(t-.5))*(1 if i<16 else .5)][w]
   v.append(max(-8,min(7,round(x*7.5-.5))))
  waves.append(v)
 return dict(waves=waves,inc=[round((2**32)*440*2**((n-69)/12)/48000) for n in range(129)],recip=[0]+[(32768+w-1)//w for w in range(1,33)],period=[12000,10000,8000,6000,5000,4000,3000,2400,2000,1600,1200,1000,800,600,400,200],tri=[0,1,2,3,4,3,2,1,0,-1,-2,-3,-4,-3,-2,-1],vib=[0,3,6,7,8,7,6,3,0,-3,-6,-7,-8,-7,-6,-3],major=[0,4,7,12]*4,minor=[0,3,7,12]*4,glitch=[0,12,-12,7,0,19,3,-5,12,0,24,7,-12,4,0,19],decay=[128,112,96,80,64,52,42,34,26,20,15,11,8,5,3,0])

def header():
 t=tables();text='/* Tables mathematiques originales generees par junior_assets.py. */\n'
 text+='static const s8 JR_WAVE[16][32] = '+str(t['waves']).replace('[','{').replace(']','}')+';\n'
 for key,typ,name in [('inc','u32','INC'),('recip','u32','WIDTH_RECIP'),('period','s32','PERIOD'),('tri','s8','TRI'),('vib','s8','VIB'),('major','s8','MAJOR'),('minor','s8','MINOR'),('glitch','s8','GLITCH'),('decay','s16','DECAY')]:
  text+=f'static const {typ} JR_{name}[] = '+'{'+','.join(str(x) for x in t[key])+'};\n'
 return text

def prepare(root,build,display_name="JUNIOR"):
 assert display_name in ("JUNIOR","ELDER")
 src=root/'tools/machines/junior';(src/'junior_tables.h').write_text(header(),encoding='utf-8')
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 obj=build/'junior.o';elf=build/'junior.elf';binary=build/'junior.bin';ld=build/'junior.ld'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-DJR_NAME="'+display_name+'"','-c',str(src/'junior.c'),'-o',str(obj)],check=True)
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); junior_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); junior_end = .; }}\n')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(r.split())==3}
 assert sy['junior_code_end']<BSS and sy['junior_end']<0x46800000
 return binary.read_bytes().ljust(sy['junior_end']-CODE,b'\0'),dict(code=CODE,bss=BSS,code_bytes=binary.stat().st_size,end=sy['junior_end'],symbols=sy,display_name=display_name,inspiration='Fors Junior',implementation='original fixed-point prototype',status='experimental',controls=['Wave','Warp','Noise','Motion'],table_editor=False,stereo_unison=False)
