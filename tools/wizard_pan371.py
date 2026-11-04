"""Wizard : toggle DATA niveau/pan, uniquement vue accueil et UI."""
from pathlib import Path
import json,hashlib,subprocess,struct,os
CODE=0x468b8000;BSS=0x468ba800;END=0x468bb000

def apply(meta,native,runtime,out,debug=False):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parents[1]
 m=meta['wizard_display']
 # Reconstruire une revision UI apres verification exacte des anciennes ecritures.
 if m.get('pan_toggle'):
  for patch in reversed(meta['wizard_pan371']['patches']):
   at=patch['at'];buf,origin=(runtime,0x46700000) if at>=0x46700000 else (native,0x40000400)
   old,new=bytes.fromhex(patch['old']),bytes.fromhex(patch['new']);offset=at-origin
   assert bytes(buf[offset:offset+len(new)])==new
   buf[offset:offset+len(old)]=old
  m=dict(m,pan_toggle=False);meta['wizard_display']=m
 base=0x46700000;nb=0x40000400;hook=m['hook'];old=bytes.fromhex(m['old']);key=0x4001c0d2
 keyold=bytes.fromhex('4e56ffa848d73c7c');assert native[key-nb:key-nb+8]==keyold
 assert m['symbols']['ws_draw']==CODE # Les wrappers plus recents conservent cette entree.
 model=meta['playability_symbols']['mi_mm_key_original'];modelold=bytes(runtime[model-base:model-base+8])
 assert modelold==bytes.fromhex('4feffff048d7003c') or (modelold[:2]==b'\x4e\xf9' and base<=int.from_bytes(modelold[2:6],'big')<base+len(runtime)),modelold.hex()
 controller=0x40077720;controllerold=bytes(native[controller-nb:controller-nb+6]);assert controllerold[:2]==b'\x4e\xf9'
 tramp='.text\n.globl ws_previous_draw\nws_previous_draw:\n.byte '+','.join(map(str,old))+f'\njmp {hook+len(old):#x}\n.globl ws_previous_key\nws_previous_key:\n.byte '+','.join(map(str,keyold))+f'\njmp {key+len(keyold):#x}\n.globl ws_previous_model_key\nws_previous_model_key:\n.byte '+','.join(map(str,modelold))+f'\njmp {model+8:#x}\n'
 tramp+='\n.globl ws_previous_controller_key\nws_previous_controller_key:\n.byte '+','.join(map(str,controllerold))+'\n'
 (out/'tramp.S').write_text(tramp);aliases=dict(m['aliases'],ws_cpu_open=meta['cpu_monitor']['symbols']['cpu_open'],ws_mod_menu=meta['fx_menu']['symbols']['menu']);ld=out/'display.ld'
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text.ws_draw) *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} ws_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); ws_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 objects=[]
 for src in (root/'tools/machines/wizard_display/display158.c',out/'tramp.S'):
  obj=out/(src.name+'.o');objects.append(obj);run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-ffunction-sections','-fno-pic','-fno-stack-protector','-DWS_VOLUME159','-DWS_PAN371',*(['-DWS_PAN_DEBUG375'] if debug else []),'-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',src,'-o',obj)
 run('ld','-T',ld,'-o',out/'display.elf',*objects);run('objcopy','-O','binary','-j','.text','-j','.data',out/'display.elf',out/'display.bin')
 raw=(out/'display.bin').read_bytes();symbols={v[2]:int(v[0],16) for line in run('nm',out/'display.elf').splitlines() if len(v:=line.split())==3}
 assert CODE+len(raw)<0x468ba000 and symbols['ws_end']<=END and symbols['ws_draw']==CODE
 patches=[]
 def write(at,old,new,buf,origin):
  offset=at-origin;assert bytes(buf[offset:offset+len(old)])==old;assert len(old)==len(new);buf[offset:offset+len(old)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 span=max(m['code_end']-CODE,len(raw));prior=bytes(runtime[CODE-base:CODE-base+span]);assert not any(prior[m['code_end']-CODE:]);write(CODE,prior,raw+bytes(span-len(raw)),runtime,base)
 assert not any(runtime[BSS-base:END-base])
 write(model,modelold,b'\x4e\xf9'+struct.pack('>I',symbols['ws_model_key'])+b'\x4e\x71',runtime,base)
 write(controller,controllerold,b'\x4e\xf9'+struct.pack('>I',symbols['ws_controller_key']),native,nb)
 meta['wizard_display']=dict(m,aliases=aliases,symbols=symbols,end=symbols['ws_end'],code_end=symbols['ws_code_end'],pan_toggle=True)
 return dict(code=CODE,code_bytes=len(raw),symbols=symbols,patches=patches,sha256=hashlib.sha256(raw).hexdigest(),UI_only=True,audio_hooks=False,native_input=model,native_input_argument_count=1,controller_input=controller,pan_source='base parameter22 stopped; live audio frame parameter22 playing',hardware_tested=False)
