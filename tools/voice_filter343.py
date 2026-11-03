"""Filtre natif des voix : quatre samples identiques, boucle dans SRAM libre."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
SITE=0x400a9d86;COUNTER=0x400a9d84;RESUME=0x400a9d9a;BASE=0x40000400

def apply(meta,native,sram,stock,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert meta.get('sram_audio',{}).get('CHORD_priority') and not meta.get('voice_filter_unroll')
 layout=meta['sram_audio'];start=0x80005268;limit=0x800062b4
 code=(max(x['at']+x['bytes'] for x in layout['modules'])+3)&~3
 body=bytes(stock[SITE-BASE:SITE-BASE+16]);assert native[SITE-BASE:SITE-BASE+16]==body
 assert native[COUNTER-BASE:COUNTER-BASE+2]==stock[COUNTER-BASE:COUNTER-BASE+2]==bytes.fromhex('7020')
 assert native[SITE-BASE+16:RESUME-BASE]==bytes.fromhex('538066ec')
 source='.text\n.globl vf_loop\nvf_loop:\n.rept 4\n.byte '+','.join(map(str,body))+f'\n.endr\n subq.l #1,%d0\n bne.w vf_loop\n jmp {RESUME:#x}\n'
 (out/'voice-filter.S').write_text(source)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 run('gcc','-mcpu=54418','-c',out/'voice-filter.S','-o',out/'voice-filter.o');run('ld','-Ttext',hex(code),'-e','vf_loop','-o',out/'voice-filter.elf',out/'voice-filter.o');run('objcopy','-O','binary',out/'voice-filter.elf',out/'voice-filter.bin')
 blob=(out/'voice-filter.bin').read_bytes();assert code+len(blob)<=limit
 offset=code-0x80000000;assert not any(sram[offset:offset+len(blob)]);sram[offset:offset+len(blob)]=blob
 patches=[]
 for at,old,new in [(COUNTER,bytes.fromhex('7020'),bytes.fromhex('7008')),(SITE,body[:6],b'\x4e\xf9'+struct.pack('>I',code))]:
  assert native[at-BASE:at-BASE+len(old)]==old;native[at-BASE:at-BASE+len(new)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 module=dict(name='voice_filter',at=code,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),symbols={'vf_loop':code})
 layout['modules'].append(module);layout['patches'].extend(patches);layout['SRAM_used']=code+len(blob)-start
 return dict(code=code,code_bytes=len(blob),sha256=module['sha256'],patches=patches,factor=4,loop_control_instructions_saved=48,net_instructions_saved_per_call=46,new_state_bytes=0,PCM_exact=True,hardware_tested=False)
