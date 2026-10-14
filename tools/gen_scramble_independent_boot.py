#!/usr/bin/env python3
"""Bootstrap compressé SCRAMBLE autonome, avec moteurs facultatifs.

Copie moteurs avant décompression du noyau ; aucun runtime Banque ajouté.
Prototype local : publication soumise aux preuves natives et combinaisons UI.
"""
import argparse,copy,json,pathlib,struct,subprocess,tempfile
import build,sprites,aplib_dense
from chord_keys_pr87 import load_stock
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE,LOADER,DECODER=0x401f8f76,0x401907a4,0x401696a0

def generate(stock,data,engine=None,chord=None):
 core=copy.deepcopy(data['core']);sc=copy.deepcopy(data['scramble'])
 start=int(core['symbols']['blob_start'],16);end=int(core['symbols']['reserved_end'],16)
 raw=bytes.fromhex(core['append']['parts'][0]['hex'])
 decoder=0x40167c50 if chord else DECODER
 chord_writes=[];pad_body='';pad_symbols=''
 if chord:
  at=int(chord['parts'][0]['dest'],16);piece=bytes.fromhex(chord['parts'][0]['hex'])
  assert at>=end
  raw+=bytes(at-start-len(raw))+piece
  chord_writes=copy.deepcopy(chord['writes'])
  pad_body='\n.globl mpu_pad\nmpu_pad:\n'+(ROOT/'tools/machines/midi_play_ui/controls.s').read_text().split('mpu_pad:',1)[1].split('    .data',1)[0]
  pad_symbols=f"CK_HELD_PADS = {chord['symbols']['held_pads']}; CK_PAD = {chord['symbols']['ck_ui_pad']}; "
  # Arrondir relativement au début du cache, lui-même non aligné à 16 KiB.
  end=start+((len(raw)+512+16383)//16384)*16384
 body=(ROOT/'tools/machines/midi_lanes/boot.s').read_text()
 body=body.replace('    movel #0x4c03e000,%d4\n    movec %d4,%acr1','    nop\n    nop\n    nop\n    nop\n    nop')
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d);(p/'boot.s').write_text(body+pad_body+'\n'+(ROOT/'tools/machines/midi_lanes/lfo_cc_depack.s').read_text())
  clear=(start+len(raw)+15)&~15
  (p/'boot.ld').write_text(pad_symbols+f'ML_PAYLOAD_SRC = {SOURCE}; ML_BANK_START = {start}; ML_BANK_SIZE = 0; ML_TG_START = {start}; ML_BANK_END = {end}; SECTIONS {{ .text.ml_loader {LOADER:#x} : {{ *(.text.ml_loader) }} .text.ml_depack {decoder:#x} : {{ *(.text.ml_depack) }} .clear {clear:#x} : {{ *(.text) }} }}')
  subprocess.run(['m68k-elf-as','-march=cfv4e','--defsym','ML_LFO_CC=1','-o',str(p/'boot.o'),str(p/'boot.s')],check=True)
  subprocess.run(['m68k-elf-ld','-T',str(p/'boot.ld'),'-o',str(p/'boot.elf'),str(p/'boot.o')],check=True)
  syms={r[2]:hex(int(r[0],16)) for line in subprocess.check_output(['m68k-elf-nm',str(p/'boot.elf')],text=True).splitlines() if len(r:=line.split())==3}
  chunks={}
  for name in ('text.ml_loader','text.ml_depack','clear'):
   subprocess.run(['m68k-elf-objcopy','-O','binary','--only-section=.'+name,str(p/'boot.elf'),str(p/'part.bin')],check=True)
   chunks[name]=(p/'part.bin').read_bytes()
 assert clear+len(chunks['clear'])<=end
 raw=bytearray(raw+bytes(clear-start-len(raw))+chunks['clear'])
 if chord:
  pad=int(syms['mpu_pad'],16);at=int(chord['symbols']['ck_ui_pad_thunk'],16)-start
  expected=bytes.fromhex('51af000451af00044ef9')+struct.pack('>I',int(chord['symbols']['ck_ui_pad'],16))
  assert raw[at:at+14]==expected;raw[at+10:at+14]=struct.pack('>I',pad)
  primary=next(w for w in chord_writes if w['off']==0x4010025c-build.BASE)
  assert primary['new']==struct.pack('>I',int(chord['symbols']['ck_ui_pad'],16)).hex();primary['new']=struct.pack('>I',pad).hex()
 raw=bytes(raw);packed=aplib_dense.pack(raw,depth=128)
 assert SOURCE+len(packed)<=build.END_LIMIT
 writes=[w for w in core['writes'] if w['off']!=0x40000530-build.BASE]+sc['writes']+chord_writes
 blocks=(end-start)//16384
 for at,value in ((0x400792f2,0x401eb750+20*blocks),(0x400792bc,0x401eb750+20*(blocks+1)+16)):
  next(w for w in writes if w['off']==at-build.BASE)['new']=struct.pack('>I',value).hex()
 for at,code in ((LOADER,chunks['text.ml_loader']),(decoder,chunks['text.ml_depack'])):
  assert len(code)<=sprites.MASKS[at][0]
  writes.extend([sprites.redirect_write(at),dict(off=at-build.BASE,old=stock[at-build.BASE:at-build.BASE+len(code)].hex(),new=code.hex())])
 if engine:
  expected=bytes.fromhex('4feffff048d700f04ef9400004ba');hits=[]
  for w in engine['writes']:
   body=bytes.fromhex(w['new'])
   hits.extend(w['off']+i for i in range(0,len(body)-len(expected)+1,2) if body[i:i+len(expected)]==expected)
  assert len(hits)==1,(engine['id'],hits)
  writes.append(dict(off=hits[0],old=expected.hex(),new='4ef9401907a4'+'4e71'*4))
 else:writes.append(dict(off=0x40000530-build.BASE,old=stock[0x40000530-build.BASE:0x4000053a-build.BASE].hex(),new='4ef9401907a44e714e71'))
 t=dict(id='scramble-independent-boot-prototype',order=50,requires=([engine['id']] if engine else []),conflicts=[],status='experimental',flashable=False,prototype_only=True,
  writes=writes,symbols=dict(core['symbols'],**sc['symbols'],**(chord['symbols'] if chord else {}),**syms),cache_blocks=blocks,
  append=dict(at=hex(SOURCE),dest=hex(start),size=len(raw),parts=[dict(dest=hex(start),hex=raw.hex())],reloc=[],compress='aplib',compressed_hex=packed.hex(),zero_pad_from=hex(build.BASE+len(stock))))
 # Ordre explicite : hook natif -> noyau -> SCRAMBLE, dans une seule recette.
 base,_=build.apply_writes(stock,[engine] if engine else []);base=bytearray(base)
 for w in writes:
  at=w['off'];old=bytes.fromhex(w['old']);new=bytes.fromhex(w['new'])
  if base[at:at+len(new)]==new:continue
  assert base[at:at+len(old)]==old,(hex(build.BASE+at),old.hex(),base[at:at+len(old)].hex())
  base[at:at+len(new)]=new
 # Fusionner les deux écritures successives du dispatcher pour le builder.
 merged={}
 for w in writes:
  if w['off'] in merged:
   previous=merged[w['off']]
   if previous==w:continue
   assert previous['new']==w['old'];previous['new']=w['new']
  else:merged[w['off']]=dict(w)
 t['writes']=sorted(merged.values(),key=lambda w:w['off'])
 build.apply_writes(stock,([engine] if engine else [])+[t])
 return t

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('cycles','candidate','output'):p.add_argument('--'+name,required=True)
 p.add_argument('--catalog');p.add_argument('--engine');p.add_argument('--check',action='store_true');a=p.parse_args()
 engine=next(t for t in json.loads(pathlib.Path(a.catalog).read_text()) if t['id']==a.engine) if a.engine else None
 t=generate(load_stock(a.cycles),json.loads(pathlib.Path(a.candidate).read_text()),engine);text=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : SCRAMBLE bootstrap autonome, un bloc cache ;',a.engine or 'sans moteurs')
if __name__=='__main__':main()
