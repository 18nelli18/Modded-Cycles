"""Comparaison SRAM : deplacer deux tables ST immuables, conserver les noyaux.

Les4172octets de tables sont copies depuis le vrai demarrage dans DDR ; les
quatre operandes de leur lecteur SRAM sont verifies avant relocation. Leur
ancienne place recoit HALL ou CHORD, le post, LOW et les boucles delay. Aucun seuil
du gouverneur, taille de ring, frequence audio ou parametre n est change.
"""
from pathlib import Path
import copy,hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
SRAM=0x80005268;SRAM_END=0x800062b4;DDR=0x467a3000;DDR_END=0x467a5000
TABLES=[(0x80005268,2088,[(0x80003e00,0x8000567c),(0x80003e20,0x80005278)]),(0x80005a90,2084,[(0x800039e4,0x80005aa0),(0x80003aa2,0x80005aa0)])]

def apply(meta,native,runtime,sram,out,include_delay=False,include_delay_filter=False,full_delay=False,prefer_chord=False):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);base=0x46700000;nb=0x40000400;sb=0x80000000
 assert not meta.get('sram_audio') and meta.get('hall_fractional_ramp')
 assert not any(runtime[DDR-base:DDR_END-base])
 assert any(e['kind']=='remove' and e['address']<=DDR and DDR_END<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 def syms(path):return {v[2]:int(v[0],16) for line in run('nm',path).splitlines() if len(v:=line.split())==3}
 def rawbytes(blob):return '.byte '+','.join(map(str,blob))+'\n'
 def link(stem,script,obj):
  ld=out/(stem+'.ld');elf=out/(stem+'.elf');binary=out/(stem+'.bin');ld.write_text(script)
  run('ld','-T',ld,'-o',elf,obj);run('objcopy','-O','binary',elf,binary);return binary.read_bytes(),syms(elf)
 # Regenerer les deux objets et verifier leur identite AVANT de les relier ailleurs.
 from hall_ramp322 import apply as hall_compile
 from post_static314 import apply as post_compile
 trial=bytearray(runtime);hall=hall_compile(copy.deepcopy(meta),trial,out/'hall',opt='-O2',fractional=True)
 assert hall['sha256']==meta['hall_merged_gain']['sha256']
 trial=bytearray(runtime);post=post_compile(copy.deepcopy(meta),bytearray(native),trial,out/'post',dry_bypass=True)
 assert post['sha256']==meta['post_static']['sha256']
 if full_delay:
  assert include_delay_filter and include_delay
  source=out/'post/post-static.S';text=source.read_text();assert text.count('.rept 4')==6
  text=text.replace('.rept 4','.rept 2').replace('moveq #8,%d6','moveq #16,%d6').replace('moveq #8,%d0','moveq #16,%d0')
  source.write_text(text);run('gcc','-mcpu=54418','-c',source,'-o',out/'post/post-static.o')
 cursor=SRAM;modules=[]
 aliases={k:v for k,v in meta['fx_menu']['symbols'].items() if k.startswith('hall_') or k in ('ps_comb','ps_ap')}
 hall_blob,hall_symbols=link('sram-hall',f'SECTIONS {{ .text {cursor:#x} : {{ *(.text*) *(.rodata*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()),out/'hall/hall-ramp.o')
 primary_blob=hall_blob;primary_symbols=hall_symbols;primary_name='hall'
 if prefer_chord:
  original=meta['chord_second'];at=original['code']-base
  assert hashlib.sha256(bytes(runtime[at:at+original['code_bytes']])).hexdigest()==original['sha256']
  src=ROOT/'tools/machines/chord_cpu/oscillator.S';flags=['-DCHORD_SECOND_FAST','-DCHORD_ECO_LOOKUP']
  run('gcc','-mcpu=54418',*flags,'-c',src,'-o',out/'chord-original.o')
  old_blob,old_symbols=link('chord-original',f'SECTIONS {{ .text {original["code"]:#x} : {{ *(.text*) }} }}\n',out/'chord-original.o')
  assert hashlib.sha256(old_blob).hexdigest()==original['sha256']
  text=src.read_text();assert text.count('.rept 4')==4
  text=text.replace('.rept 4','.rept 2').replace('moveq #8,%d0','moveq #16,%d0')
  for macro in ['TWO 0','TWO 1','ONE 0','ONE 1']:
   block='#ifdef CHORD_SECOND_FAST\n '+macro+'\n '+macro+'\n#endif';assert text.count(block)==1;text=text.replace(block,'')
  (out/'chord-compact.S').write_text(text);run('gcc','-mcpu=54418',*flags,'-c',out/'chord-compact.S','-o',out/'chord-compact.o')
  primary_blob,primary_symbols=link('sram-chord',f'SECTIONS {{ .text {cursor:#x} : {{ *(.text*) }} }}\n',out/'chord-compact.o');primary_name='chord'
 modules.append(dict(name=primary_name,at=cursor,bytes=len(primary_blob),sha256=hashlib.sha256(primary_blob).hexdigest(),symbols=primary_symbols));cursor=(cursor+len(primary_blob)+3)&~3
 post_blob,post_symbols=link('sram-post',f'SECTIONS {{ .text {cursor:#x} : {{ *(.text*) }} }}\n',out/'post/post-static.o')
 modules.append(dict(name='post',at=cursor,bytes=len(post_blob),sha256=hashlib.sha256(post_blob).hexdigest(),symbols=post_symbols));cursor=(cursor+len(post_blob)+3)&~3
 # Les deux LOW utilisent la meme paire de samples ; A5 est deja sauve par
 # leur prologue natif et reste mort jusqu a la restauration de l epilogue.
 fl=meta['filter_unroll'];starts=fl['symbols'];bodies=[];resumes=[]
 for name in ['fl_low','fl_lohi_low']:
  at=starts[name]-base;blob=bytes(runtime[at:at+540]);body=blob[:132]
  assert blob[:528]==body*4 and blob[528:532]==bytes.fromhex('b3ca6600') and blob[534:536]==b'\x4e\xf9'
  assert int.from_bytes(blob[532:534],'big',signed=True)==-532
  bodies.append(body);resumes.append(int.from_bytes(blob[536:540],'big'))
 assert bodies[0]==bodies[1]
 asm='.text\n'
 for name,resume in zip(['sr_low','sr_lohi_low'],resumes):asm+=f'.globl {name}\n{name}:\n lea {resume:#x},%a5\n bra.w sr_low_loop\n'
 pairs=2 if include_delay_filter and not prefer_chord else 4
 asm+=f'.globl sr_low_loop\nsr_low_loop:\n.rept {pairs}\n'+rawbytes(bodies[0])+'.endr\n cmpa.l %a2,%a1\n bne.w sr_low_loop\n jmp (%a5)\n'
 (out/'sram-low.S').write_text(asm);run('gcc','-mcpu=54418','-c',out/'sram-low.S','-o',out/'sram-low.o')
 low_blob,low_symbols=link('sram-low',f'SECTIONS {{ .text {cursor:#x} : {{ *(.text*) }} }}\n',out/'sram-low.o')
 modules.append(dict(name='low',at=cursor,bytes=len(low_blob),sha256=hashlib.sha256(low_blob).hexdigest(),symbols=low_symbols));cursor+=len(low_blob);assert cursor<=SRAM_END
 delay_symbols=None
 if include_delay:
  cursor=(cursor+3)&~3;old_delay=meta['delay_static'];at=old_delay['code']-base
  assert hashlib.sha256(bytes(runtime[at:at+old_delay['code_bytes']])).hexdigest()==old_delay['sha256']
  slow=int.from_bytes(bytes.fromhex(old_delay['patches'][0]['old'])[2:],'big')
  run('gcc','-mcpu=54418','-c',ROOT/'tools/machines/track_fx/delay-static307.S','-o',out/'sram-delay.o')
  delay_blob,delay_symbols=link('sram-delay',f'SECTIONS {{ .text {cursor:#x} : {{ *(.text*) }} }}\nds_old = {slow:#x};\n',out/'sram-delay.o')
  modules.append(dict(name='delay',at=cursor,bytes=len(delay_blob),sha256=hashlib.sha256(delay_blob).hexdigest(),symbols=delay_symbols));cursor+=len(delay_blob);assert cursor<=SRAM_END
 delay_filter_source=None
 if include_delay_filter:
  assert include_delay
  site=0x400575e0;old=bytes(native[site-nb:site-nb+6]);assert old[:2]==b'\x4e\xf9'
  delay_filter_source=int.from_bytes(old[2:],'big');assert 0x46700000<=delay_filter_source<0x46701000
  a=delay_filter_source-base;delay_filter_blob=bytes(runtime[a:a+268]);assert delay_filter_blob[:256]==delay_filter_blob[:64]*4
  assert delay_filter_blob[256:262]==bytes.fromhex('53806600fefc') and delay_filter_blob[262:]==bytes.fromhex('4ef940057624')
  cursor=(cursor+3)&~3
  modules.append(dict(name='delay_filter',at=cursor,bytes=len(delay_filter_blob),sha256=hashlib.sha256(delay_filter_blob).hexdigest(),symbols={'sr_delay_filter':cursor}));cursor+=len(delay_filter_blob);assert cursor<=SRAM_END
 extras=[];extra_blobs=[]
 if full_delay:
  from native_fx_unroll301 import SPECS
  for name,counter,loop,end,resume,was,now in SPECS:
   if name not in ('delay_input','delay_feedback_a','delay_feedback_b'):continue
   old=bytes(native[loop-nb:loop-nb+6]);assert old[:2]==b'\x4e\xf9';source=int.from_bytes(old[2:],'big');assert 0x46700000<=source<0x46701000
   n=end-loop;size=4*n+12;a=source-base;blob=bytes(runtime[a:a+size]);assert blob[:4*n]==blob[:n]*4
   assert blob[4*n+2:4*n+4]==b'\x66\x00' and int.from_bytes(blob[4*n+4:4*n+6],'big',signed=True)==-(4*n+4)
   assert blob[-6:]==b'\x4e\xf9'+struct.pack('>I',resume)
   cursor=(cursor+3)&~3;modules.append(dict(name=name,at=cursor,bytes=size,sha256=hashlib.sha256(blob).hexdigest(),symbols={'sr_'+name:cursor}))
   extras.append(dict(site=loop,source=source,target=cursor));extra_blobs.append(blob);cursor+=size;assert cursor<=SRAM_END,(name,cursor-SRAM)
 moved=[];operand_patches=[];destination=DDR
 empty_lite=not meta['activity_masks']['full']
 if empty_lite:
  assert not any(sram[SRAM-sb:SRAM_END-sb])
  assert all(not any(sram[at-sb-2:at-sb+4]) for source,size,refs in TABLES for at,old in refs)
 for source,size,refs in TABLES:
  if empty_lite:continue
  data=bytes(sram[source-sb:source-sb+size]);runtime[destination-base:destination-base+size]=data
  for at,old in refs:
   off=at-sb;assert sram[off-2:off] in (b'\x20\x3c',b'\x22\x3c') and sram[off:off+4]==struct.pack('>I',old)
   new=destination+old-source;sram[off:off+4]=struct.pack('>I',new);operand_patches.append(dict(at=at,old=old,new=new))
  moved.append(dict(source=source,target=destination,bytes=size,sha256=hashlib.sha256(data).hexdigest()));destination=(destination+size+31)&~31
 assert destination<=DDR_END
 sram[SRAM-sb:SRAM_END-sb]=bytes(SRAM_END-SRAM)
 for module,blob in zip(modules,[primary_blob,post_blob,low_blob]+([delay_blob] if include_delay else [])+([delay_filter_blob] if include_delay_filter else [])+extra_blobs):sram[module['at']-sb:module['at']-sb+len(blob)]=blob
 patches=[]
 def patch(at,old,new):
  bank,off=(native,at-nb) if at<base else (runtime,at-base);assert bank[off:off+len(old)]==old,(hex(at),bank[off:off+len(old)].hex(),old.hex())
  bank[off:off+len(new)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 for item in extras:patch(item['site'],b'\x4e\xf9'+struct.pack('>I',item['source']),b'\x4e\xf9'+struct.pack('>I',item['target']))
 if prefer_chord:
  patch(0x400a8906,b'\x4e\xf9'+struct.pack('>I',meta['chord_second']['symbols']['chord_fast']),b'\x4e\xf9'+struct.pack('>I',primary_symbols['chord_fast']))
 else:
  hall_entry=meta['fx_menu']['symbols']['fx_hall'];patch(hall_entry,b'\x4e\xf9'+struct.pack('>I',meta['hall_merged_gain']['symbols']['fx_hall']),b'\x4e\xf9'+struct.pack('>I',hall_symbols['fx_hall']))
 for p in meta['post_static']['patches']:
  name='ps_drive' if p['at']==0x4005707a else 'ps_blend';patch(p['at'],bytes.fromhex(p['new']),b'\x4e\xf9'+struct.pack('>I',post_symbols[name]))
 if delay_filter_source is not None:
  module=next(x for x in modules if x['name']=='delay_filter');patch(0x400575e0,b'\x4e\xf9'+struct.pack('>I',delay_filter_source),b'\x4e\xf9'+struct.pack('>I',module['at']))
 if delay_symbols:
  p=meta['delay_static']['patches'][0];patch(p['at'],bytes.fromhex(p['new']),b'\x4e\xf9'+struct.pack('>I',delay_symbols['ds_gate']))
 for p,name in zip(fl['patches'],['sr_low','sr_lohi_low']):patch(p['at'],bytes.fromhex(p['new']),b'\x4e\xf9'+struct.pack('>I',low_symbols[name]))
 return dict(modules=modules,tables=moved,operand_patches=operand_patches,patches=patches,SRAM_used=cursor-SRAM,SRAM_reclaimed=SRAM_END-SRAM,table_bytes=sum(t['bytes'] for t in moved),CHORD_priority=prefer_chord,filter_pairs_per_iteration=pairs,post_samples_per_iteration=2 if full_delay else 4,DSP_arithmetic_unchanged=True,governor_unchanged=True,hardware_tested=False)
