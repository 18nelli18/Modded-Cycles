"""PUNCH23 : source MIT100demons intacte ; UI et art provenant du paquet0.5."""
import subprocess,struct,json,hashlib,re
CODE=0x468a0000;ART=0x468ae000;BSS=0x468af000;END=0x468b0000
def prepare(root,build,fast=False,peak=False):
 root=root.resolve();src=root/'tools/machines/punch';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 upstream=json.loads((src/'UPSTREAM.json').read_text())
 for name,want in upstream['sha256'].items():assert hashlib.sha256((src/name).read_bytes()).hexdigest()==want,(name,'source guard')
 manifest=json.loads((src/'manifest.json').read_text());obj=build/'punch.o';labels=build/'punch-labels.c';lo=build/'punch-labels.o'
 flags=manifest['build']['cflags']+(['-O3'] if peak else [])
 source=src/'punch.c'
 if fast:
  from punch_fast143 import source as fast_source
  source=fast_source(src,build)
 subprocess.run([cross+'gcc.exe',*flags,'-c',str(source),'-o',str(obj)],check=True)
 labels.write_text('const char punch_name[]="PUNCH";\nconst char punch_labels[5][8]={"Index","Model","Ratio","Env","Decay"};\nconst char punch_short_labels[5][8]={"Idx","MODL","RTIO","Env","DEC"};\n')
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-c',str(labels),'-o',str(lo)],check=True)
 ld=build/'punch.ld';elf=build/'punch.elf';binary=build/'punch.bin'
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); punch_code_end = .; .data : {{ *(.data*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); punch_end = .; }}')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj),str(lo)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 assert sy['punch_code_end']<ART and sy['punch_end']<END
 profile=dict(machine=23,name='PUNCH',icon='upstream-punch',**{'class':'PERC'},style='FM',str=5,dex=3,mag=5)
 blob=bytearray(binary.read_bytes().ljust(sy['punch_end']-CODE,b'\0'));pos=ART+56
 art=(src/'punch_icons.h').read_text()
 for desc,tag,w,h in [(ART,'A',48,33),(ART+28,'B',34,34)]:
  ptrs=[]
  for plane in ('IMG','MSK'):
   words=re.search('PUNCH_'+plane+'_'+tag+r'\[\d+\]\s*=\s*\{(.*?)\}',art,re.S)[1]
   values=[int(v,16) for v in re.findall(r'0x[0-9a-fA-F]+',words)];raw=struct.pack('>'+str(len(values))+'I',*values)
   if tag=='A':
    from build_machine_identity_test import stats,encode
    raw=stats(profile) if plane=='IMG' else encode([[1]*w for _ in range(h)])
   assert len(raw)==w*((h+31)//32)*4;ptrs.append(pos);blob[pos-CODE:pos-CODE+len(raw)]=raw;pos+=len(raw)
  blob[desc-CODE:desc-CODE+28]=struct.pack('>7I',0x401117c8,w,h,2,*ptrs,0)
 assert pos<BSS
 return bytes(blob),dict(code=CODE,bss=BSS,end=sy['punch_end'],code_bytes=binary.stat().st_size,symbols=sy,machine=23,models=12,model_names=['KIK','TOM','BNG','CNG','TAI','TIM','MAR','DJB','BLK','GNG','BUB','ZAP'],defaults=[64,0,68,40,50],profile=profile,upstream=upstream,source_unmodified=not fast,pcm_exact_optimization=fast,peak_optimization=peak,hardware_tested=False,status='experimental')
