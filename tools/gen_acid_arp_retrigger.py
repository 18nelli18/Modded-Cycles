"""Relance ACID sous arp/retrig sur les bases2.63 epinglees ; note209."""
from pathlib import Path
import argparse,hashlib,json,math,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x46932000;BSS=0x4693f800;S=R/'tools/machines/acid'
def main():
 p=argparse.ArgumentParser()
 for k in ('source','metadata','cycles','output'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--check',action='store_true')
 a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest();raw=a.source.read_bytes();m=json.loads(a.metadata.read_text());assert sha(raw)==m['sha256'];assert m['sha256'] in ('266fe30abce8297b8a997fa598d3481789a5226a6742a0fad8e74b5f25271d47', '42fb95265a18d609a53674777583e41137a52f1cee6ceca58af5a8aa46248e60', 'daa7a92c71893b030be2645a66ce03ff9c5c1e5961cd180b7f7e222b86a6fe9d')
 assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
 _,_,stock,ops=read(a.cycles);info,pkg,image,_=read(a.source);image=bytearray(image);O=a.output;O.mkdir(parents=True,exist_ok=True)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 full=True;assert 'ae_mode' in m['per_track_fx']['symbols']
 aliases=dict(ar_old_tracks=m['per_track_fx']['symbols']['trk'])
 from gen_governor_recovery_test import TAIL
 at=m['per_track_fx']['symbols']['ae_update'];end=int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE;old=bytes(image[end+at-TAIL:end+at-TAIL+8]);assert old==bytes.fromhex('4fefffd048d77cfc')
 (O/'trampoline.S').write_text('.text\n.globl ar_old_update\nar_old_update:\n.byte '+','.join(map(str,old))+f'\njmp {at+8:#x}\n')
 objects=[]
 for src in (R/'tools/machines/acid_arp/retrigger.c',O/'trampoline.S'):
  obj=O/(src.stem+'.o');run('gcc','-mcpu=54418','-Os','-ffunction-sections','-fdata-sections','-Wno-unused-function','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',src,'-o',obj);objects.append(obj)
 (O/'module.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) . += 4; }} aa_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 run('ld','-T',O/'module.ld','--gc-sections','-e','ar_update','-o',O/'module.elf',*objects);run('objcopy','-O','binary',O/'module.elf',O/'module.bin');sy={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=BSS and sy['aa_end']<0x46940000
 oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
 # La continuation native ne revient pas : installer avant le saut de fin.
 load=f'.text\n.globl aa_load\naa_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(sy["aa_end"]-BSS+3)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n'
 hooks=[]
 at=m['per_track_fx']['symbols']['ae_update'];hooks.append(dict(at=at,target=sy['ar_update']));load+=f' lea {at:#x},%a0\n move.l #0x4ef9,%d0\n move.w %d0,(%a0)+\n move.l #{sy["ar_update"]:#x},%d0\n move.l %d0,(%a0)\n'
 load+=f' movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n';(O/'load.S').write_text(load)
 run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','aa_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
 struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob
 from title204_assets import apply as apply_title
 def title_patch(at,old,new,buf):
  assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
 m['title_screen']=apply_title(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,title_patch,'2.64',lite=not full,previous=m['title_screen'])
 dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),ops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
 plains=[]
 for sec in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
 result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_2.64_ACID_Arp_Retrigger_Test.syx'
 if a.check:assert target.read_bytes()==result
 else:target.write_bytes(result)
 m.update(sha256=sha(result),main_os_sha256=sha(image),acid_arp=dict(loader=loader,previous_loader=oldentry,code=CODE,code_bytes=len(blob),bss=BSS,bss_end=sy['aa_end'],symbols=sy,hooks=hooks,flash_bytes=len(rebuilt),hardware_tested=False,full=full));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT ACID arp retrigger',len(blob),'code bytes',len(rebuilt),'flash bytes',flush=True)
if __name__=='__main__':main()
