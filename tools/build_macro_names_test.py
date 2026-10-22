"""Popup MACRO nomme, deux variantes privees sur les candidats identites v15.

La table confirme les index 0..46 de gen_macro.MODELS. Seul le slot UI144 est
detourne ; le runtime compresse et le son restent identiques au candidat source.
"""
import hashlib,json,os,struct,subprocess
from pathlib import Path
from mtlib import aplib,container
from mtlib.syx import unwrap,wrap,BYTES_PER_MSG
import aplib_grow
from gen_macro import MODELS

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/firmware'
BASE=0x40000400;START=0x401aa140-BASE;TAIL=0x467ab360;ORIGIN=0x467c6000
SLOT=0x401005bc;DELEGATE=0x401ba5ec
SOURCE=ROOT/'tools/machines/macro'
NAMES=[
 ('CSAW','CSAW',''),('Morph','Morph',''),('Saw + Square','Saw +','Square'),
 ('Sine + Triangle','Sine +','Triangle'),('Buzz','Buzz',''),('Square + Sub','Square','+ Sub'),
 ('Saw + Sub','Saw + Sub',''),('Square Sync','Square','Sync'),('Saw Sync','Saw Sync',''),
 ('Triple Saw','Triple Saw',''),('Triple Square','Triple','Square'),('Triple Triangle','Triple','Triangle'),
 ('Triple Sine','Triple','Sine'),('Triple Ring Mod','Triple','Ring Mod'),('Saw Swarm','Saw Swarm',''),
 ('Saw Comb','Saw Comb',''),('Toy','Toy',''),('Digital Lowpass','Digital LP',''),
 ('Digital Peak','Digital PK',''),('Digital Bandpass','Digital BP',''),('Digital Highpass','Digital HP',''),
 ('VOSIM','VOSIM',''),('Vowel','Vowel',''),('Vowel FOF','Vowel FOF',''),('Harmonics','Harmonics',''),
 ('FM','FM',''),('Feedback FM','Feedback','FM'),('Chaotic Feedback FM','Chaotic','FB FM'),
 ('Plucked','Plucked',''),('Bowed','Bowed',''),('Blown','Blown',''),('Fluted','Fluted',''),
 ('Struck Bell','Struck','Bell'),('Struck Drum','Struck','Drum'),('Kick','Kick',''),
 ('Cymbal','Cymbal',''),('Snare','Snare',''),('Wavetables','Wavetables',''),('Wave Map','Wave Map',''),
 ('Wave Line','Wave Line',''),('Wave Paraphonic','Wave','Paraphonic'),('Filtered Noise','Filtered','Noise'),
 ('Twin Peaks Noise','Twin Peaks','Noise'),('Clocked Noise','Clocked','Noise'),
 ('Granular Cloud','Granular','Cloud'),('Particle Noise','Particle','Noise'),
 ('Digital Modulation','Digital','Modulation')]

def read(path):
 stream,info=unwrap(path.read_bytes());pkg=container.parse(stream)
 section=next(s for s in pkg['sections'] if s['id']==3)
 image,ops=aplib.depack(pkg['blob'][section['off']:section['off']+section['size']])
 return info,pkg,image,ops

def main():
 assert len(NAMES)==len(MODELS)==47
 assert all(len(line)<=10 for _,a,b in NAMES for line in [a,b])
 build=OUT/'macro-names-v16';build.mkdir(exist_ok=True)
 labels=[dict(index=i,model=MODELS[i],name=n,lines=[a]+([b] if b else [])) for i,(n,a,b) in enumerate(NAMES)]
 (build/'macro_model_labels.inc').write_text('static const char *const macro_model_lines[47][2]={\n'+',\n'.join('{'+json.dumps(a)+','+json.dumps(b)+'}' for _,a,b in NAMES)+'\n};\n')
 cross=str(ROOT.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 obj=build/'names.o';elf=build/'names.elf';binary=build/'names.bin';ld=build/'names.ld'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-stack-protector','-I',str(build),'-c',str(SOURCE/'model_names.c'),'-o',str(obj)],check=True)
 ld.write_text(f'SECTIONS {{ .text {ORIGIN:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); macro_names_end = .; }}\nPROVIDE(macro_names_original = {DELEGATE:#x});\n')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
 sy={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(r.split())==3}
 code=binary.read_bytes().ljust(sy['macro_names_end']-ORIGIN,b'\0');assert ORIGIN+len(code)<0x46800000
 official=ROOT/'firmware/model-cycles_OS1.13.syx';oi,op,stock,ops=read(official)
 device=json.loads((ROOT/'tweaks/model-cycles_OS1.13/device.json').read_text());assert hashlib.sha256(official.read_bytes()).hexdigest()==device['stock_syx_sha256']
 plains=[]
 for s in op['sections']:
  try:plains.append(aplib.depack(op['blob'][s['off']:s['off']+s['size']])[0])
  except Exception:pass
 key=container.find_key(plains,op['blob'][:-container.DIGEST_LEN],op['blob'][-container.DIGEST_LEN:]);assert key
 for prefix,expected in [('all-features','2b8da1cd8be34cadd6f6db83900473c1580c1085b112a480041b259c9386d99b'),('no-filter','41559fab2ce3784ab262cb35173be6f5e8bd932aa379181b8728f50147450a08')]:
  source=OUT/(prefix+'-machine-identity-test-v15.syx');meta=json.loads(source.with_suffix('.json').read_text())
  assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['sha256']==expected
  info,pkg,image,_=read(source);prefix_bytes=bytearray(image[:START])
  assert int.from_bytes(prefix_bytes[SLOT-BASE:SLOT-BASE+4],'big')==DELEGATE
  tail_start=int.from_bytes(prefix_bytes[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
  tail=bytearray(image[tail_start:]);assert TAIL+len(tail)<ORIGIN
  tail.extend(bytes(ORIGIN-TAIL-len(tail)));tail.extend(code)
  struct.pack_into('>I',prefix_bytes,SLOT-BASE,sy['macro_names_popup'])
  struct.pack_into('>I',prefix_bytes,0x40195ad8-BASE,len(tail))
  data=bytes(prefix_bytes)+image[START:tail_start]+bytes(tail)
  assert data[START:tail_start]==image[START:tail_start]
  allowed=set(range(SLOT-BASE,SLOT-BASE+4))|set(range(0x40195ad8-BASE,0x40195adc-BASE))
  assert {i for i,(a,b) in enumerate(zip(prefix_bytes,image[:START])) if a!=b}<=allowed
  dirty=bytearray(len(data));dirty[:START]=bytes(a!=b for a,b in zip(prefix_bytes,stock));dirty[START:]=b'\1'*(len(data)-START)
  section=aplib_grow.repack_grow(data,ops,dirty,START);assert aplib.depack(section)[0]==data
  rebuilt=container.rebuild(op,{3:section},key)
  raw=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),oi['product'],oi['start_seq'])
  dest=OUT/(prefix+'-macro-names-test-v16.syx');dest.write_bytes(raw)
  _,final,after,_=read(dest);assert after==data
  for s in op['sections']:
   if s['id']==3:continue
   t=next(t for t in final['sections'] if t['id']==s['id']);assert op['blob'][s['off']:s['off']+s['size']]==final['blob'][t['off']:t['off']+t['size']]
  meta.update(base=source.name,base_sha256=expected,sha256=hashlib.sha256(raw).hexdigest(),main_os_sha256=hashlib.sha256(data).hexdigest(),macro_model_names=labels,macro_names_symbols=sy,macro_model_descriptor=102,macro_names_delegate=DELEGATE,runtime_tail_end=hex(ORIGIN+len(code)),hardware_tested=False,release=None,main_changed=False)
  dest.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
  print('BUILT',dest.name,meta['sha256'],'popup only; compressed runtime exact',flush=True)

if __name__=='__main__':main()
