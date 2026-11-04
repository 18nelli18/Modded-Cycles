"""Double PATTERN : verrou UI du selecteur natif, sans hook audio/IRQ."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
BASE=0x46700000;NB=0x40000400
CODE=0x4679f600;BSS=0x4679ffc0;END=0x467a0000;SITE=0x40020a7a

def apply(meta,native,runtime,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert not meta.get('pattern_latch374') and not meta.get('chorus370')
 assert not any(runtime[CODE-BASE:END-BASE])
 old=bytes.fromhex('4e56ff8848d73cfc')
 assert bytes(native[SITE-NB:SITE-NB+8])==old
 pop=0x40024af0;popold=bytes.fromhex('4feffff448d70c04');assert bytes(native[pop-NB:pop-NB+8])==popold
 (out/'old.S').write_text('.text\n.globl pl_old_key\npl_old_key:\n.byte '+','.join(map(str,old))+f'\njmp {SITE+8:#x}\n.globl pl_old_popup_key\npl_old_popup_key:\n.byte '+','.join(map(str,popold))+f'\njmp {pop+8:#x}\n')
 (out/'latch.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} pl_end = .; .data 0 : {{ *(.data*) }} /DISCARD/ : {{ *(.comment) *(.note.GNU-stack) }} }}\nASSERT(ADDR(.text)+SIZEOF(.text)<={BSS:#x},"code plein")\nASSERT(SIZEOF(.data)==0,"donnees initialisees interdites")\nASSERT(pl_end<={END:#x},"etat plein")\n')
 with (out/'latch.ld').open('a') as f:f.write('pl_old_popup_frame = 0x400749b4;\n')
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
 os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*a):return subprocess.check_output([cross+t+'.exe',*map(str,a)],text=True)
 objects=[]
 for source in (ROOT/'tools/machines/direct_jump/pattern-latch374.c',out/'old.S'):
  obj=out/(source.name+'.o');objects.append(obj)
  run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-common','-fwrapv','-Wall','-Wextra','-Werror','-c',source,'-o',obj)
 run('ld','--orphan-handling=error','-T',out/'latch.ld','-o',out/'latch.elf',*objects)
 run('objcopy','-O','binary',out/'latch.elf',out/'latch.bin');blob=(out/'latch.bin').read_bytes()
 symbols={p[2]:int(p[0],16) for line in run('nm',out/'latch.elf').splitlines() if len(p:=line.split())==3}
 new=b'\x4e\xf9'+struct.pack('>I',symbols['pl_key'])+b'\x4e\x71'
 popnew=b'\x4e\xf9'+struct.pack('>I',symbols['pl_popup_key'])+b'\x4e\x71'
 frame=0x401011b0;frameold=struct.pack('>I',0x400749b4);assert bytes(native[frame-NB:frame-NB+4])==frameold
 framenew=struct.pack('>I',symbols['pl_popup_frame']);native[frame-NB:frame-NB+4]=framenew
 native[SITE-NB:SITE-NB+8]=new;native[pop-NB:pop-NB+8]=popnew;runtime[CODE-BASE:CODE-BASE+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),bss=BSS,state_bytes=symbols['pl_end']-BSS,symbols=symbols,patches=[dict(region='native',at=SITE,old=old.hex(),new=new.hex()),dict(region='native',at=pop,old=popold.hex(),new=popnew.hex()),dict(region='native',at=frame,old=frameold.hex(),new=framenew.hex()),dict(region='runtime',at=CODE,old=bytes(len(blob)).hex(),new=blob.hex())],sha256=hashlib.sha256(blob).hexdigest(),audio_hooks_changed=False,physical_held_override=False,native_popup_timeout_suspended=True,hardware_tested=False)
