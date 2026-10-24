"""SPEAK prive : trois formants originaux, lexique phonemique sans ROM tierce."""
import json,math,subprocess,os,struct
from pathlib import Path
CODE=0x46818000;BSS=0x46824000;END=0x46828000
# Parametres originaux du prototype : frequences/bandes en Hz, duree en ms.
PHONES={
'SIL':(500,1500,2500,100,120,160,0,0,15,0),
'AA':(730,1090,2440,80,100,150,230,0,130,0),'AE':(660,1720,2410,90,110,160,230,0,125,0),
'AH':(640,1190,2390,90,110,160,230,0,115,0),'AO':(570,840,2410,80,100,160,230,0,115,0),
'AX':(500,1500,2500,100,120,180,210,0,70,0),'EH':(530,1840,2480,80,110,170,230,0,105,0),
'ER':(490,1350,1690,90,100,130,230,0,120,0),'IH':(390,1990,2550,80,110,180,230,0,100,0),
'IY':(270,2290,3010,70,100,160,230,0,110,0),'UH':(440,1020,2240,90,100,170,230,0,100,0),
'UW':(300,870,2240,80,100,170,230,0,125,0),
'L':(400,1200,2400,100,140,180,210,0,75,0),'R':(350,1300,1600,100,100,140,210,0,80,0),
'W':(300,700,2200,100,120,180,200,0,65,0),'Y':(250,2200,3000,100,120,180,200,0,65,0),
'M':(250,900,2200,70,170,220,180,0,90,0),'N':(260,1500,2400,70,180,240,180,0,85,0),
'NG':(280,1800,2600,70,180,240,180,0,90,0),
'F':(600,1600,3100,250,350,450,0,150,100,0),'V':(600,1600,3100,250,350,450,140,90,85,0),
'S':(1200,2800,3700,300,400,450,0,220,120,0),'Z':(1200,2800,3700,300,400,450,130,150,100,0),
'SH':(500,1900,3200,220,300,380,0,210,120,0),'ZH':(500,1900,3200,220,300,380,130,130,100,0),
'TH':(600,1600,3000,250,350,450,0,140,100,0),'DH':(600,1600,3000,250,350,450,150,70,70,0),
'H':(500,1500,2500,150,220,300,0,100,80,0),
'P':(400,900,2100,250,350,450,0,210,45,1),'B':(400,900,2100,180,250,350,130,150,45,1),
'T':(1000,2500,3500,250,350,450,0,220,45,1),'D':(500,1800,2900,180,250,350,150,160,45,1),
'K':(600,1900,3000,250,350,450,0,220,50,1),'G':(400,1600,2600,180,250,350,150,160,50,1),
'CH':(500,2000,3300,220,300,380,0,220,110,0)}

def header(root,smooth=False,soft=False):
 words=json.loads((root/'tools/machines/speak/words.json').read_text());assert len(words)==128
 assert len({w['word'] for w in words})==128
 assert all(0<len(w['word'])<=9 and 0<len(w['phones'])<=13 and all(p in PHONES for p in w['phones']) for w in words)
 ids={p:i for i,p in enumerate(PHONES)};phones=list(PHONES.values());rows=[]
 for w in words:
  row=[ids['SIL']]+[ids[p] for p in w['phones']]+[ids['SIL'],255];assert len(row)<=16;rows.append(row+[255]*(16-len(row)))
 banks=[]
 for bank in range(16):
  ratio=2**((bank-8)/24);br=[]
  for f1,f2,f3,b1,b2,b3,vo,noise,ms,stop in phones:
   rr=[]
   for k,(freq,bw) in enumerate(zip((f1,f2,f3),(b1,b2,b3))):
    r=math.exp(-math.pi*bw*(1.45 if soft and noise else 1)/8000);f=min(3800,freq*ratio)
    weights=(1,.75,.5)
    if smooth and noise:
     # Fricatives : retirer le grondement F1, conserver le souffle F2/F3.
     weights=((.10,.8,.45) if list(PHONES)[len(br)] in ('S','Z') else (.16,.8,.45)) if soft else ((.12,.9,.7) if list(PHONES)[len(br)] in ('S','Z') else (.2,.85,.6))
    rr.append([round(2*r*math.cos(2*math.pi*f/8000)*16384),round(-r*r*16384),round((1-r)*4096*weights[k])])
   br.append(rr)
  banks.append(br)
 arr=lambda v:str(v).replace('[','{').replace(']','}')
 text='/* Tables mathematiques et pronunciations originales ; speak_assets.py. */\n'
 text+='static const Phone SP_PHONES[]='+arr([[ms*8,vo,round(noise*((.35 if name in ('S','Z') else .4 if name in ('SH','ZH') else .5) if soft else (.7 if name in ('S','Z') else .8))) if smooth else noise,stop] for name,(f1,f2,f3,b1,b2,b3,vo,noise,ms,stop) in PHONES.items()])+';\n'
 text+='static const Resonator SP_RESONATORS[16]['+str(len(phones))+'][3]='+arr(banks)+';\n'
 text+='static const u8 SP_WORDS[128][16]='+arr(rows)+';\n'
 text+='static const char SP_NAMES[128][10]='+arr([w['word'] for w in words]).replace("'",'"')+';\n'
 text+='static const u32 SP_INC[129]='+arr([round(2**32*min(3000,140*2**((n-60)/12))/8000) for n in range(129)])+';\n'
 return text,words

def microphone():
 p=[[0]*34 for _ in range(34)]
 for y in range(3,22):
  for x in range(12,22):
   if (6<=y<=18 or 14<=x<=19):p[y][x]=1
 for y in (7,10,13,16):
  for x in range(14,20):p[y][x]=0
 for y in range(14,23):p[y][8]=p[y][9]=p[y][24]=p[y][25]=1
 for x in range(10,24):p[24][x]=p[25][x]=1
 for y in range(25,30):p[y][16]=p[y][17]=1
 for x in range(11,23):p[30][x]=p[31][x]=1
 from build_machine_identity_test import encode
 return encode(p)

def prepare(root,build,previous_popup,clear=False,smooth=False,level=False,soft=False,speed_fix=False):
 src=root/'tools/machines/speak';text,words=header(root,smooth=smooth,soft=soft);(src/'speak_tables.h').write_text(text,encoding='utf-8')
 compile_src=src/'speak.c'
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 obj=build/'speak.o';elf=build/'speak.elf';binary=build/'speak.bin';ld=build/'speak.ld'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DSP_CLEAR=1'] if clear else []),*(['-DSP_SMOOTH=1'] if smooth else []),*(['-DSP_LEVEL=1'] if level else []),*(['-DSP_SOFT=1'] if soft else []),*(['-DSP_SPEED_FIX=1'] if speed_fix else []),'-c',str(compile_src),'-o',str(obj)],check=True)
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); speak_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); speak_end = .; }}\nspeak_previous_popup = {previous_popup:#x};\n')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert sy['speak_code_end']<BSS and sy['speak_end']<END
 profile=dict(machine=20,name='SPEAK',icon='microphone',**{'class':'VOICE'},style='TALK',str=1,dex=5,mag=5)
 from build_machine_identity_test import stats,encode
 assert sy['speak_code_end']<=0x46823000
 blob=bytearray(binary.read_bytes().ljust(sy['speak_end']-CODE,b'\0'));pos=0x46823038
 for desc,pixels,w,h in [(0x46823000,stats(profile),48,33),(0x4682301c,microphone(),34,34)]:
  mask=encode([[1]*w for _ in range(h)]);ptr=pos;blob[pos-CODE:pos-CODE+len(pixels)]=pixels;pos+=len(pixels);mp=pos;blob[pos-CODE:pos-CODE+len(mask)]=mask;pos+=len(mask);blob[desc-CODE:desc-CODE+28]=struct.pack('>7I',0x401117c8,w,h,2,ptr,mp,0)
 assert pos<BSS
 return bytes(blob),dict(stats_descriptor=0x46823000,icon_descriptor=0x4682301c,code=CODE,bss=BSS,end=sy['speak_end'],code_bytes=binary.stat().st_size,symbols=sy,machine=20,name='SPEAK',profile=profile,words=[w['word'] for w in words],controls=['Voice','Word','Speed','Articulation'],status='experimental',hardware_tested=False,implementation='original fixed-point formant speech, not TI ROM emulation',speech_rate=8000,clarity=clear and not smooth,smooth_consonants=smooth,level_calibrated=level,soft_consonants=soft,speed_idle_fixed=speed_fix,output_scale=(524288 if level else 16384 if clear else 8192),output_gain_db=(36.1236 if level else 6.0206 if clear else 0))
