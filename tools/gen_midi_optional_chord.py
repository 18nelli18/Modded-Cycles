#!/usr/bin/env python3
"""Reloge ChordKeys derrière la Banque privée ; conserve les pads HARMONY.

Manifeste local non flashable ; MIT PR87, aucune routine firmware copiée.
"""
import argparse,copy,json,pathlib,struct,subprocess,tempfile
from chord_keys_pr87 import load_stock
from gen_chord_keys_compat import generate as place
from gen_chord_independent_payload import generate as isolate

def generate(stock,data,layout,prebuilt):
 start=int(data['symbols']['ML_BANK_END'],16)
 old=min(int(r['at'],16) for r in layout if r['kind']=='bank')
 layout=copy.deepcopy(layout)
 for row in layout:
  if row['kind']=='bank':row['at']=hex(int(row['at'],16)-old+start)
 neutral={'id':'chord-private-container','ram_only_rollback':True,'midi_reclaim':{'free_spans':[[hex(start),hex(start+16384)]]},'writes':[], 'symbols':{},'append':{'dest':hex(start),'parts':[{'dest':hex(start),'hex':bytes(16384).hex()}]}}
 chord,container=place(stock,layout,None,neutral,prebuilt);payload=isolate(chord,container)
 origin=int(payload['parts'][0]['dest'],16);raw=bytes.fromhex(payload['parts'][0]['hex']);at=(origin+len(raw)+15)&~15
 pad=(pathlib.Path(__file__).parent/'machines/midi_play_ui/controls.s').read_text().split('mpu_pad:',1)[1].split('    .data',1)[0]
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d);(p/'p.s').write_text('.text\n.globl mpu_pad\nmpu_pad:\n'+pad+'\n.balign 16\n')
  (p/'p.ld').write_text(f"CK_HELD_PADS = {payload['symbols']['held_pads']}; CK_PAD = {payload['symbols']['ck_ui_pad']}; SECTIONS {{ .text {at:#x} : {{ *(.text) }} }}")
  subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(p/'p.o'),str(p/'p.s')],check=True)
  subprocess.run(['m68k-elf-ld','-T',str(p/'p.ld'),'-o',str(p/'p.elf'),str(p/'p.o')],check=True)
  subprocess.run(['m68k-elf-objcopy','-O','binary',str(p/'p.elf'),str(p/'p.bin')],check=True);helper=(p/'p.bin').read_bytes()
 raw=bytearray(raw+bytes(at-origin-len(raw))+helper)
 thunk=int(payload['symbols']['ck_ui_pad_thunk'],16)-origin
 assert raw[thunk:thunk+14]==bytes.fromhex('51af000451af00044ef9')+struct.pack('>I',int(payload['symbols']['ck_ui_pad'],16))
 raw[thunk+10:thunk+14]=struct.pack('>I',at)
 primary=next(w for w in payload['writes'] if w['off']==0x4010025c-0x40000400);primary['new']=struct.pack('>I',at).hex()
 payload['parts'][0]['hex']=raw.hex();payload['symbols']['mpu_pad']=hex(at)
 payload['relocation_audit']=chord['relocation_audit'];payload['flashable']=False
 out=copy.deepcopy(data);out['extra_runtime']=payload
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--compiled',required=True);p.add_argument('--layout',required=True);p.add_argument('--prebuilt',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();read=lambda f:json.loads(pathlib.Path(f).read_text())
 out=generate(load_stock(a.cycles),read(a.compiled),read(a.layout),read(a.prebuilt));text=json.dumps(out,indent=1,ensure_ascii=False)+'\n';path=pathlib.Path(a.output)
 if a.check:assert path.read_text()==text
 else:path.write_text(text)
 print('ok : fragments Chord privés relogés, pads natifs sans TRIG ; non flashable')
if __name__=='__main__':main()
