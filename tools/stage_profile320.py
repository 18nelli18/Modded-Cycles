"""Quatre marqueurs natifs avec contrats registres/CCR, lecture RPC seulement."""
from pathlib import Path
import os,struct,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1];CODE=0x4679f000;BSS=0x467a0000;END=BSS+256
SITES=[(0x4005980a,8),(0x40059824,6),(0x40059858,10),(0x40059878,8),(0x4005979e,8),(0x400597ba,10),(0x400597cc,8),(0x40058ca6,6)]
def remove(meta,native,runtime):
 base=0x46700000;nb=0x40000400;previous=meta['stage_profile']
 assert hashlib.sha256(bytes(runtime[CODE-base:CODE-base+previous['code_bytes']])).hexdigest()==previous['sha256']
 for patch in previous['patches']:
  at=patch['at'];buf,offset=(native,at-nb) if at<base else (runtime,at-base);new=bytes.fromhex(patch['new']);assert buf[offset:offset+len(new)]==new;buf[offset:offset+len(new)]=bytes.fromhex(patch['old'])
 runtime[CODE-base:END-base]=bytes(END-CODE)
def apply(meta,native,runtime,out):
 base=0x46700000;nb=0x40000400;out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if meta.get('stage_profile'):
  remove(meta,native,runtime)
 assert not any(runtime[CODE-base:END-base])
 rp=meta['remote_panel'];s=rp['symbols'];fs=meta['fx_menu']['symbols'];ig=meta['complete_irq_accounting']['symbols'];aliases=dict(st_enabled=meta['dx_symbols']['dx_enabled'],st_old_request=s['rp_request'],st_old_send=s['rp_send'],st_old_reverb=fs['fx_reverb'],st_old_delay=fs['fx_delay'],st_irq_t0=ig['gb_irq_t0'],st_old_finish=ig['fg_finish'])
 asm='.text\n';markers=[]
 for i,(at,size) in enumerate(SITES):
  raw=bytes(native[at-nb:at-nb+size]);assert raw[:2]!=b'\x4e\xf9';name='st_marker'+str(i);markers.append(dict(at=at,size=size,old=raw.hex(),symbol=name))
  asm+=f'.balign 4\n.globl {name}\n{name}:\n lea -20(%sp),%sp\n movem.l %d0-%d1/%a0-%a1,(%sp)\n move.w %sr,%d0\n move.l %d0,16(%sp)\n pea {i}\n jsr st_mark\n addq.l #4,%sp\n move.l 16(%sp),%d0\n move.w %d0,%sr\n movem.l (%sp),%d0-%d1/%a0-%a1\n lea 20(%sp),%sp\n.byte '+','.join(map(str,raw))+f'\n jmp {at+size:#x}\n'
 (out/'stage-profile.S').write_text(asm)
 (out/'stage-profile.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) }} st_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*args):return subprocess.check_output([cross+t+'.exe',*map(str,args)],text=True)
 run('gcc','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/track_fx/stage-profile320.c','-o',out/'stage-profile.o');run('gcc','-mcpu=54418','-c',out/'stage-profile.S','-o',out/'stage-markers.o')
 run('ld','-T',out/'stage-profile.ld','-o',out/'stage-profile.elf',out/'stage-profile.o',out/'stage-markers.o');run('objcopy','-O','binary',out/'stage-profile.elf',out/'stage-profile.bin');blob=(out/'stage-profile.bin').read_bytes()
 symbols={v[2]:int(v[0],16) for line in run('nm',out/'stage-profile.elf').splitlines() if len(v:=line.split())==3};assert CODE+len(blob)<=BSS and symbols['st_end']<=END
 patches=[]
 for mark in markers:
  at=mark['at'];new=b'\x4e\xf9'+struct.pack('>I',symbols[mark['symbol']])+b'\x4e\x71'*((mark['size']-6)//2);native[at-nb:at-nb+len(new)]=new;patches.append(dict(at=at,old=mark['old'],new=new.hex()))
 for oldfn,newfn in [('rp_request','st_request'),('rp_send','st_send')]:
  expected=b'\x4e\xb9'+struct.pack('>I',s[oldfn]);sites=[p['at'] for p in rp['patches'] if p['new']==expected.hex()];assert len(sites)==1;at=sites[0];assert runtime[at-base:at-base+6]==expected;new=b'\x4e\xb9'+struct.pack('>I',symbols[newfn]);runtime[at-base:at-base+6]=new;patches.append(dict(at=at,old=expected.hex(),new=new.hex()))
 for oldfn,newfn in [('fx_reverb','st_reverb'),('fx_delay','st_delay')]:
  expected=b'\x4e\xb9'+struct.pack('>I',fs[oldfn]);sites=[i for i in range(0,len(runtime)-5,2) if runtime[i:i+6]==expected];assert len(sites)==1,(oldfn,sites)
  offset=sites[0];new=b'\x4e\xb9'+struct.pack('>I',symbols[newfn]);runtime[offset:offset+6]=new;patches.append(dict(at=base+offset,old=expected.hex(),new=new.hex()))
 expected=b'\x4e\xf9'+struct.pack('>I',ig['fg_finish']);at=meta['per_track_fx']['symbols']['gb_finish'];offset=at-base;assert runtime[offset:offset+6]==expected
 new=b'\x4e\xf9'+struct.pack('>I',symbols['st_finish']);runtime[offset:offset+6]=new;patches.append(dict(at=at,old=expected.hex(),new=new.hex()))
 runtime[CODE-base:CODE-base+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_bytes=symbols['st_end']-BSS,symbols=symbols,aliases=aliases,markers=markers,patches=patches,sha256=hashlib.sha256(blob).hexdigest(),hardware_tested=False,DSP_unchanged=True,stage_labels=['voices','filter_and_levels','FX_and_output'])
