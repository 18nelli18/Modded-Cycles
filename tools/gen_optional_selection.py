"""Prototype prive : meme runtime fixe pour les524288 masques de machines.
Les moteurs exclus sont inaccessibles au selecteur et muets ; leurs octets
DSP restent embarques. Aucune reduction de taille/RAM n'est revendiquee.
"""
from pathlib import Path
import json,sys,subprocess,struct,hashlib,os,argparse
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'tools/machines/optional_selection';sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from gen_governor_recovery_test import read,BASE,START,RUNTIME,TAIL
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
import aplib_grow
CODE=0x468d0600;MASK=0x468d0ff0
def split(p):
 info,pkg,main,ops=read(p);end=int.from_bytes(main[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE;raw=main[START:end];rt,rtops=aplib.depack(struct.pack('>II',len(raw),sum(raw)&0xffffffff)+raw)
 return info,pkg,main,ops,bytearray(main[:START]),bytearray(rt),bytearray(main[end:]),rtops
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',required=True,type=Path);parser.add_argument('--metadata',required=True,type=Path);parser.add_argument('--cycles',required=True,type=Path);parser.add_argument('--cross',required=True);parser.add_argument('--expected-sha256',default='c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6');parser.add_argument('--lite-sha256',default='0a6e67c552c3a799cb4090357ebe8018503efdebaae9ad3aaa3e68b5f3bd4e0e');parser.add_argument('--output',type=Path,default=ROOT/'build/optional-selection');args=parser.parse_args();output=args.output;output.mkdir(parents=True,exist_ok=True);source=args.base;meta=json.loads(args.metadata.read_text(encoding='utf-8'));assert hashlib.sha256(source.read_bytes()).hexdigest()==args.expected_sha256==meta['sha256']
 info,pkg,original,ops,prefix,rt,tail,rtops=split(source);before=[bytes(prefix),bytes(rt),bytes(tail)]
 def section(at):return (prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL)
 def peek(at,n):a,b=section(at);return bytes(a[at-b:at-b+n])
 edits=[]
 def patch(at,data):
  a,b=section(at);old=peek(at,len(data));assert len(old)==len(data);a[at-b:at-b+len(data)]=data;edits.append(dict(at=at,old=old.hex(),new=data.hex()))
 def jump(at,to):patch(at,b'\x4e\xf9'+struct.pack('>I',to))
 sy=json.loads((WORK/'midi-symbols.json').read_text());fx=meta['fx_menu']['symbols'];p=meta['playability_symbols']
 cross=args.cross;os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','');tramp='.text\n';gates=[]
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 def gate(name,at,machine,disabled='zero',stack=True):
  nonlocal tramp
  raw=peek(at,32)
  if raw[:2]==b'\x4e\xf9':old=int.from_bytes(raw[2:6],'big')
  else:
   n=0
   for i in cs.disasm(raw,at):
    assert not i.mnemonic.startswith(('b','j')) and 'pc' not in i.op_str.lower(),(name,hex(at),i.mnemonic,i.op_str)
    n+=i.size
    if n>=6:break
   assert n>=6
   tramp+=f'.globl old_{name}\nold_{name}:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';old='old_'+name
  label='opt_gate_'+name;bit=machine-6
  # Sauvegarder aussi le SR : les callbacks WAVE void conservent tout l'etat.
  restore=' move.w (%sp),%d1\n move.w %d1,%sr\n movem.l 4(%sp),%d0-%d1\n lea 12(%sp),%sp\n'
  tramp+=f'.globl {label}\n{label}:\n lea -12(%sp),%sp\n movem.l %d0-%d1,4(%sp)\n move.w %sr,%d1\n move.w %d1,(%sp)\n move.l opt_mask,%d0\n btst #{bit},%d0\n beq 1f\n'+restore+f' jmp {old if isinstance(old,str) else hex(old)}\n1:\n'+restore
  tramp+=(' rts\n' if disabled=='void' else f' jmp {disabled}\n' if disabled.startswith('opt_') or disabled.startswith('0x') else ' moveq #0,%d0\n rts\n')
  gates.append((at,label))
 # Services navigateur : le chemin installe rejoue le code d'origine exact.
 for label,at in [('wave_tick',0x4677a996),('wave_note',0x4677a750)]:gate(label,at,14,'void')
 gate('wave_yes',0x4677a79a,14);gate('wave_predicate',0x467a9a90,14)
 for name in ('dx7_service','dx7_browser_key','dx7_browser_encoder','dx7_browser_draw','dx7_status_draw','dx7_library_load','dx7_library_save'):
  if name in meta['legacy']['symbols']:gate(name,meta['legacy']['symbols'][name],21)
 gate('midi_live',sy['mm_live_on'],17,'opt_midi_live');gate('midi_sequence',p['mm_sequence'],17,'opt_midi_sequence');gate('midi_cc',p['mm_cc_put'],17)
 gate('midi_mout',sy['mm_mout'],17,hex(sy['mm_mout_original']))
 for name in ('mm_encoder','mm_draw','mm_ui_key','mm_audio_poll'):gate(name,sy[name],17)
 (output/'gates.S').write_text(tramp)
 objects=[]
 for src in (WORK/'selection.c',WORK/'selection.S',output/'gates.S'):
  obj=output/(src.name+'.o');subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src),'-o',str(obj)],check=True);objects.append(str(obj))
 ld=output/'optional.ld';ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); opt_code_end = .; .optmask {MASK:#x} : {{ *(.optmask) }} }}\n'+''.join(f'PROVIDE({k} = {fx[k]:#x});\n' for k in ('machine_valid','machine_stamp','machine_result')))
 elf=output/'optional.elf';binary=output/'optional.bin';subprocess.run([cross+'ld.exe','-T',str(ld),'-e','opt_dispatch','-o',str(elf),*objects],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
 symbols={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert meta['filter_modes']['symbols']['fc_extra_end']<=CODE<symbols['opt_code_end']<=MASK;blob=binary.read_bytes();assert not any(peek(CODE,len(blob)))
 patch(CODE,blob)
 assert peek(0x467886fa,6)==bytes.fromhex('b08465000084');jump(0x467886fa,symbols['opt_dispatch'])
 for at,target in [(fx['fx_machine_step'],'opt_fx_step'),(meta['tiny_extra']['symbols']['tiny_menu_increment'],'opt_increment'),(meta['tiny_extra']['symbols']['marks'],'opt_marks')]:jump(at,symbols[target])
 for at,label in gates:jump(at,symbols[label])
 packed=aplib.repack(bytes(rt),rtops,bytes(a!=b for a,b in zip(rt,before[1])));assert aplib.depack(packed)[0]==bytes(rt)
 oldend=int.from_bytes(original[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 packed+=bytes((-(len(packed)-8-(oldend-START)))&3)
 shift=len(packed)-8-(oldend-START);relocations=[]
 if 'direct_jump' in meta:
  first=meta['direct_jump']['loader'];last=int.from_bytes(original[0x40195adc-BASE:0x40195ae0-BASE],'big')
  sparse=meta.get('acid_articulation',meta.get('wizard_priority'))
  loaders=(first,sparse['previous_loader'],last) if sparse else (first,last)
  for loader in loaders:
   span=512 if sparse and loader==last else 124
   for offset in range(loader-BASE,loader-BASE+span,2):
    value=int.from_bytes(original[offset:offset+4],'big')
    if first<=value<BASE+len(original):
     relocations.append(dict(at=BASE+offset,old=value));struct.pack_into('>I',tail,offset-oldend,value+shift)
  assert len(relocations)==(5 if sparse else 3)
  struct.pack_into('>I',prefix,0x40195adc-BASE,last+shift)
 struct.pack_into('>I',prefix,0x40195ad0-BASE,BASE+START+len(packed)-8)
 main=bytes(prefix)+packed[8:]+bytes(tail)
 _,_,stock,stockops=read(args.cycles);assert len(stock)==START
 dirty=bytes(a!=b for a,b in zip(prefix,stock))+b'\1'*(len(main)-START);section3=aplib_grow.repack_grow(main,stockops,dirty,START)
 from bootstrap205_assets import pack as safe_pack
 section3,packing=safe_pack(section3)
 import importlib.util
 spec=importlib.util.spec_from_file_location('verified_aplib',ROOT/'tools/mtlib/aplib.py');verified=importlib.util.module_from_spec(spec);spec.loader.exec_module(verified)
 assert verified.depack(section3,bootstrap_gap=0x1ffc00)[0]==main
 plains=[]
 for sec in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:section3},key);assert len(rebuilt)<=0x1c0000
 raw=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);(output/'universal-all.syx').write_bytes(raw)
 manifest=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),lite_sha256=args.lite_sha256,source_build=meta.get('per_track_fx',{}).get('source_build',215),source_release=meta.get('release','2.56'),universal_sha256=hashlib.sha256(raw).hexdigest(),main_sha256=hashlib.sha256(main).hexdigest(),code=CODE,code_bytes=len(blob),mask=MASK,mask_main_offset=START+len(packed)-8+MASK-TAIL,symbols=symbols,patches=edits,packing=packing,embedded_unselected_dsp=True,flash_bytes=len(rebuilt),selection_bits=19,variants=524288)
 manifest['base_loader_relocations']=relocations
 (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('BUILT universal',len(blob),'module bytes;',len(rebuilt),'flash bytes;',manifest['universal_sha256'],flush=True)
if __name__=='__main__':main()
