"""UI3.48 : libelles Wizard synchrones et intro Genie independante de l'audio.

Le rafraichissement de ui_gran n'appelle les getters que depuis UI (IPL0).
Le timeout Genie garde sa duree, sur GPT au lieu de blk_clk endormi.
Aucun hook audio, etat nouveau, seuil ou parametre de synthese modifie.
"""
from pathlib import Path
import hashlib,os,struct,subprocess
BASE=0x40000400;CODE=0x467a6000;LIMIT=0x467a6800
CLOCK=0x401b11a4;INTRO_TIME=0x40159ae8;TICKS_PER_BLOCK=90112
LABEL_SITE=0x401b25d8;GRAN_WATCH=0x401bb0d4;UI_GRAN=0x401bcdfc

def apply(meta,native,runtime,out):
 assert not meta.get('ui_fixes348') and not any(runtime[CODE-0x46700000:LIMIT-0x46700000])
 assert any(x['kind']=='remove' and x['address']<=CODE and LIMIT<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
 old_label=b'\x43\xf9'+struct.pack('>I',UI_GRAN);assert native[LABEL_SITE-BASE:LABEL_SITE-BASE+6]==old_label
 source=f'''.text
.globl entry
entry:
 move.l %d1,-(%sp)
 move.w %sr,%d0
 andi.l #0x700,%d0
 bne.w cached
 jsr {GRAN_WATCH:#x}
cached:
 move.l (%sp)+,%d1
 lea {UI_GRAN:#x},%a1
 jmp {LABEL_SITE+6:#x}
'''
 out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'ui-fixes.S').write_text(source)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):subprocess.check_call([cross+tool+'.exe',*map(str,args)])
 run('gcc','-mcpu=54418','-c',out/'ui-fixes.S','-o',out/'ui-fixes.o');run('ld','-Ttext',hex(CODE),'-e','entry','-o',out/'ui-fixes.elf',out/'ui-fixes.o');run('objcopy','-O','binary',out/'ui-fixes.elf',out/'ui-fixes.bin')
 blob=(out/'ui-fixes.bin').read_bytes();assert CODE+len(blob)<=LIMIT
 patches=[]
 def patch(at,old,new):
  assert len(old)==len(new) and native[at-BASE:at-BASE+len(old)]==old,hex(at)
  native[at-BASE:at-BASE+len(old)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 patch(LABEL_SITE,old_label,b'\x4e\xf9'+struct.pack('>I',CODE))
 clock=b'\x20\x39'+struct.pack('>I',CLOCK);sites=[BASE+i for i in range(0,len(native)-6,2) if native[i:i+6]==clock];assert len(sites)==2,sites
 tick,new=sites
 assert native[tick-BASE+6:tick-BASE+12]==b'\x90\xb9'+struct.pack('>I',INTRO_TIME)
 assert native[new-BASE+6:new-BASE+12]==b'\x23\xc0'+struct.pack('>I',INTRO_TIME)
 for at in sites:patch(at,clock,b'\x20\x39'+struct.pack('>I',0xfc07000c))
 assert native[tick-BASE+12:tick-BASE+14]==b'\x0c\x80'
 blocks=int.from_bytes(native[tick-BASE+14:tick-BASE+18],'big');assert blocks in (750,1500)
 timeout=blocks*TICKS_PER_BLOCK
 patch(tick+12,b'\x0c\x80'+struct.pack('>I',blocks),b'\x0c\x80'+struct.pack('>I',timeout))
 runtime[CODE-0x46700000:CODE-0x46700000+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),patches=patches,genie_tick_clock=tick,genie_open_clock=new,timeout_ticks=timeout,original_timeout_blocks=blocks,UI_only=True,audio_hooks=False,new_state_bytes=0,hardware_tested=False)
