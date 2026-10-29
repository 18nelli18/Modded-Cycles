"""Banc leger uniquement : pas de nouvelles instances de reverbe/delay."""
from pathlib import Path
import subprocess,json,os,re,argparse,hashlib
WORK=Path(__file__).resolve().parent;ROOT=Path(os.environ.get('CREATURE_ROOT','H:/CREATURE-source/retrosyn-integration-step-rec-solo'))
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--code',type=lambda x:int(x,0),default=0x47000000);parser.add_argument('--bss',type=lambda x:int(x,0),default=0x47010000);parser.add_argument('--output',type=Path,default=WORK/'light-build');parser.add_argument('--extra',action='append',type=Path,default=[]);parser.add_argument('--roots',type=Path);parser.add_argument('--aliases',type=Path);args=parser.parse_args();OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'tools/machines';cross=os.environ.get('M68K_CROSS','H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');vendor=os.environ.get('MACRO_VENDOR','H:/CREATURE-source/retrosyn-integration/build/macro-vendor/eurorack');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','');objects=[]
def compile(name,text,flags):
 p=OUT/(name+'.c');p.write_text(text,encoding='utf-8');obj=OUT/(name+'.o');subprocess.run([cross+'gcc.exe','-mcpu=54418',*flags,'-ffunction-sections','-fdata-sections','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Wno-unused-function','-I',str(WORK),'-I',str(WORK.parent/'pots'),'-I',str(source/'fx_menu'),'-I',str(source/'stereo_chorus'),'-I',str(source/'delay_crush_send'),'-c',str(p),'-o',str(obj)],check=True);objects.append(str(obj));return obj
definitions=json.loads(args.aliases.read_text()) if args.aliases else {}
no_vinyl=bool(definitions.get('build_no_vinyl',0))
compile('routing',('#define MF_NO_VINYL 1\n' if no_vinyl else '')+(WORK/'light-routing.c').read_text(),['-O3'])
chorus=(source/'stereo_chorus/chorus.c').read_text(encoding='utf-8').split('void ch_process(',1)[0]
chorus=chorus.replace('struct ch_state ch_state;','struct ch_state lt_ch1_state,lt_ch2_state;').replace('sample(u32 c,','sample(struct ch_state *s,u32 c,').replace('ch_state.ring','s->ring').replace('void ch_chorus(s32 *out,','__attribute__((noinline,noclone)) static void chorus_shared(struct ch_state *s,s32 *out,').replace('struct ch_state *s=&ch_state;s32 speed','s32 speed').replace('sample(c,s->write','sample(s,c,s->write')
for n in (1,2):chorus+=f'\nvoid lt_ch{n}(s32*out,const s32*in,const s16*p,u32 mode,u32 gain){{chorus_shared(&lt_ch{n}_state,out,in,p,mode,gain);}}\n'
chorus+='\nvoid lt_ch_reset(void){struct ch_state *s[2]={&lt_ch1_state,&lt_ch2_state};for(u32 n=0;n<2;n++){s[n]->write=s[n]->phase=s[n]->drift=s[n]->active=s[n]->gain=s[n]->ready=s[n]->filled=s[n]->prior_gain=0;for(u32 c=0;c<2;c++)s[n]->pre[c]=s[n]->post[c]=s[n]->delay[c]=0;}}\n'
compile('chorus-shared',chorus,['-O3'])
extra=(source/'fx_menu/extra.c').read_text(encoding='utf-8').split('\n#ifdef FX_GATED\n/* Meme reseau',1)[0];assert 'void fx_gated' not in extra
start=extra.index('void fx_ring(');end=extra.index('#ifdef FX_INPUT_FIX\nstatic s32 psat',start)
assert hashlib.sha256(extra[start:end].encode()).hexdigest()=='71af92bb1d5708ee0de6c94ae49ce4c7416da67de1e1d86753f3ff405517c00d'
extra=extra[:start]+(WORK/'ring-fast.c').read_text()+extra[end:]
compile('mod',extra,['-O3','-DFX_EXTRA=1','-DFX_GATED96=1','-DFX_INPUT_FIX=1',*[f'-Dfx_{n}=lt_{n}' for n in ('extra_reset','ring','phaser','ring_freq','ring_depth','phase_rate','phase_depth','phase_feedback')]])
vinyl=(source/'fx_menu/dsp.c').read_text(encoding='utf-8').split('/* Mixeur EMAC natif.',1)[0]
vinyl=vinyl.replace('static s32 gain_aux[2][6],left[192],right[192],aux[64],effect[64],correction[64];','').replace('static u32 active,ready,gain=256,prior_gain=256,correction_on;','')
vinyl=vinyl.replace('static u32 dust_seed[2]={0x5a17c9e3u,0xc41d8b27u},dust_target[2],dust_gain[2];','static u32 dust_seed[2]={0x5a17c9e3u,0xc41d8b27u},dust_gain[2];u32 dust_target[2];')
if not no_vinyl:
 obj=compile('vinyl',vinyl,['-O3','-fno-unroll-loops','-DFX_DUST=1','-Ddust_target=lt_dust_target',*[f'-Dfx_{n}=lt_{n}' for n in ('vinyl','vinyl_reset','crackle','warble','wspeed')]])
 subprocess.run([cross+'objcopy.exe','--globalize-symbol=lt_dust_target',str(obj)],check=True)
crush=(source/'delay_crush_send/crush.c').read_text(encoding='utf-8').split('void cr_process(',1)[0];crush=re.sub(r'struct cr_state \{[^\n]+\};','struct cr_state {struct quant_state echo;};',crush)
crush=crush.replace('struct cr_state cr_state;','struct cr_state lt_cr_state,lt_cr2_state;').replace('static void crush(','__attribute__((noinline,noclone)) static void crush(')
crush=crush.replace('void cr_crush(s32 *out,const s32 *in,u32 rate,u32 bits){crush(&cr_state.echo,out,in,rate,bits);}','void lt_crush(s32 *out,const s32 *in,u32 rate,u32 bits){crush(&lt_cr_state.echo,out,in,rate,bits);}'+'\nvoid lt_crush2(s32 *out,const s32 *in,u32 rate,u32 bits){crush(&lt_cr2_state.echo,out,in,rate,bits);}')
crush+='\nvoid lt_crush_reset(void){lt_cr_state.echo=(struct quant_state){0};lt_cr2_state.echo=(struct quant_state){0};}\n'
compile('crush-shared',crush,['-O3','-funroll-loops','-DCR_LEAN_FX=1'])
for p in args.extra:
 if p.suffix.lower()=='.c':compile(p.stem,p.read_text(encoding='utf-8'),['-O2' if p.stem in ('lfo-idle','filter-low','filter-modes','fx-idle','lfo-sync','pots') else '-O3' if p.stem in ('firmware-bridge','governor','irq-budget','acid-envelope-dsp') else '-Os','-fwrapv',*(['-funroll-loops'] if p.stem=='acid-envelope-dsp' else []),*(['-fno-tree-loop-distribute-patterns'] if p.stem=='pots' else [])])
 elif p.suffix.lower()=='.cc':
  obj=OUT/(p.name+'.o');subprocess.run([cross+'g++.exe','-mcpu=54418','-O2','-fno-exceptions','-fno-rtti','-fno-threadsafe-statics','-fno-use-cxa-atexit','-fno-pic','-fno-common','-ffunction-sections','-fdata-sections','-fomit-frame-pointer','-I',vendor,'-c',str(p),'-o',str(obj)],check=True);objects.append(str(obj))
 else:
  obj=OUT/(p.name+'.o');subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(p),'-o',str(obj)],check=True);objects.append(str(obj))
aliases=json.loads(args.aliases.read_text()) if args.aliases else {}

ld=OUT/'light.ld';ld.write_text(f'SECTIONS {{ .text {args.code:#x} : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss {args.bss:#x} (NOLOAD) : {{ lt_bss_start = .; *(.bss*) *(COMMON) lt_bss_end = .; }} }}\nPROVIDE(ch_native = 0x400579c4);\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()),encoding='utf-8')
elf=OUT/'light.elf';binary=OUT/'light.bin';subprocess.run([cross+'ld.exe','-T',str(ld),'-e','mf_sum6',*(['--gc-sections',*sum((['--undefined',root] for root in json.loads(args.roots.read_text())),[])] if args.roots else []),'-Map',str(OUT/'light.map'),'-o',str(elf),*objects],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert args.code+len(binary.read_bytes())<=args.bss;report=dict(symbols=sy,code=args.code,bss=args.bss,laboratory_only=not args.extra,firmware_hooks_installed=False,shared_reverb_delay_unchanged=True,code_bytes=len(binary.read_bytes()),bss_bytes=sy['lt_bss_end']-sy['lt_bss_start'],types=['Off','Chorus I','Chorus II','Vinyl','Ring Mod','Phaser','Crusher 1','Crusher 2']);(OUT/'light.json').write_text(json.dumps(report,indent=2)+'\n');print('BUILT LIGHT MODULE:',report['code_bytes'],'code/data bytes;',report['bss_bytes'],'state bytes; no firmware image',flush=True)





