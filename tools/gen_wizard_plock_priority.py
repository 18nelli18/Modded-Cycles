"""Correctif Wizard seul sur les bases2.62 epinglees ; note208, titre2.63."""
from pathlib import Path
import argparse,hashlib,json,math,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x46931000;BSS=0x4693e000;S=R/'tools/machines/acid'
def main():
 p=argparse.ArgumentParser()
 for k in ('source','metadata','cycles','output'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--check',action='store_true')
 a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest();raw=a.source.read_bytes();m=json.loads(a.metadata.read_text());assert sha(raw)==m['sha256'];assert m['sha256'] in ('c74daa751796ebf79a52bac28083ca0d36f859cfde85dce1272700f8c998a380','666fb41df056d9093396c6e031eea392a0a8a08d218e3dcb802d335b574c8569','895058fc6391b2b3183096c0a95cd3c7b78b489b986ba4328530be5cd251a3e7','3c4fbd44fc8222c9b392e08b068bf04f8a768b44b842df75c6b65953e34158a1','4829f71e6bc1cb0632de7ce37c7eb2ff2349681f2d13d54f372d12cc7fc23fa6')
 assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
 _,_,stock,ops=read(a.cycles);info,pkg,image,_=read(a.source);image=bytearray(image);O=a.output;O.mkdir(parents=True,exist_ok=True)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 full='ae_mode' in m['per_track_fx']['symbols'];songrow=12 if full else 11
 aliases={**m['direct_jump']['aliases'],**m['direct_jump']['symbols']}
 aliases['wp_mask_pointer']=m['beat_repeat_symbols']['br_mask_address']
 aliases['aa_old_key']=int.from_bytes(image[0x40077722-BASE:0x40077726-BASE],'big')
 aliases['aa_old_encoder']=int.from_bytes(image[0x400775fa-BASE:0x400775fe-BASE],'big')
 for name,at in [('encode',0x4005d18a),('decode',0x4005d3dc),('new',0x4000f906)]:aliases['sg_old_'+name]=int.from_bytes(image[at+2-BASE:at+6-BASE],'big')
 aliases['sg_old_frame']=aliases['jp_frame']
 aliases={k:v for k,v in aliases.items() if isinstance(v,int) and k.replace('_','').isalnum()}
 aliases.update(sg_old_switch=int.from_bytes(image[0x40055c5e-BASE:0x40055c62-BASE],'big'),sg_old_mute_irq=int.from_bytes(image[0x40058ca8-BASE:0x40058cac-BASE],'big'))
 (O/'entry.c').write_text('typedef unsigned int u32;extern void wp_before(const u32*),wp_after(void);extern u32 aa_old_encoder(u32,const u32*);u32 aa_face_encoder(u32 v,const u32*e){wp_before(e);u32 r=aa_old_encoder(v,e);wp_after();return r;}')
 objects=[]
 for src in (R/'tools/machines/wizard_priority/control.c',O/'entry.c'):
  obj=O/(src.stem+'.o');run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',src,'-o',obj);objects.append(obj)
 (O/'module.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} aa_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 run('ld','-T',O/'module.ld','-e','aa_face_encoder','-o',O/'module.elf',*objects);run('objcopy','-O','binary',O/'module.elf',O/'module.bin');sy={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=BSS and sy['aa_end']<0x46940000
 oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
 # La continuation native ne revient pas : installer avant le saut de fin.
 load=f'.text\n.globl aa_load\naa_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(sy["aa_end"]-BSS+3)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n'
 hooks=[]
 at=0x400775f8;hooks.append(dict(at=at,target=sy['aa_face_encoder']));load+=f' lea {at:#x},%a0\n move.l #0x4ef9,%d0\n move.w %d0,(%a0)+\n move.l #{sy["aa_face_encoder"]:#x},%d0\n move.l %d0,(%a0)\n'
 load+=f' movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n';(O/'load.S').write_text(load)
 run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','aa_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
 struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob
 from title204_assets import apply as apply_title
 def title_patch(at,old,new,buf):
  assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
 m['title_screen']=apply_title(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,title_patch,'2.63',lite=not full,previous=m['title_screen'])
 dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),ops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
 plains=[]
 for sec in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
 result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_2.63_Wizard_Plock_Priority.syx'
 if a.check:assert target.read_bytes()==result
 else:target.write_bytes(result)
 m.update(sha256=sha(result),main_os_sha256=sha(image),wizard_priority=dict(loader=loader,previous_loader=oldentry,code=CODE,code_bytes=len(blob),bss=BSS,bss_end=sy['aa_end'],symbols=sy,hooks=hooks,flash_bytes=len(rebuilt),hardware_tested=False,full=full));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT Wizard priority',len(blob),'code bytes',len(rebuilt),'flash bytes',flush=True)
if __name__=='__main__':main()
