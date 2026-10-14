#!/usr/bin/env python3
"""Extraire les seules réserves ChordKeys du conteneur Banque MIDI.

Prototype non flashable : le bootstrap indépendant reste à intégrer/prover.
Les hooks et adresses Chord restent identiques ; aucun hook Banque/TG inclus.
--chord recette --bank recette --output manifeste [--check]
"""
import argparse,copy,hashlib,json,pathlib
import aplib_cost

def generate(chord,bank):
 reservations=sorted(chord['bank_reservations'],key=lambda r:int(r['at'],16))
 start=min(int(r['at'],16) for r in reservations);end=max(int(r['at'],16)+r['size'] for r in reservations)
 source=bytes.fromhex(bank['append']['parts'][0]['hex']);source_start=int(bank['append']['parts'][0]['dest'],16)
 raw=bytearray(end-start);used=0
 for r in reservations:
  at=int(r['at'],16);n=r['size'];assert source_start<=at and at+n<=source_start+len(source)
  raw[at-start:at-start+n]=source[at-source_start:at-source_start+n];used+=n
 for left,right in zip(reservations,reservations[1:]):assert int(left['at'],16)+left['size']<=int(right['at'],16)
 owned=[(int(r['at'],16),int(r['at'],16)+r['size']) for r in reservations]
 owned.extend((0x40000400+w['off'],0x40000400+w['off']+len(bytes.fromhex(w['new']))) for w in chord['writes'] if len(w['new'])>64)
 # Chaque symbole propre est fourni par Chord, jamais par les helpers Banque.
 for name,value in chord['symbols'].items():
  address=int(value,16);assert any(lo<=address<hi for lo,hi in owned),(name,value)
 packed=aplib_cost.pack(bytes(raw),depth=512,lazy=True)
 return {'kind':'chord-independent-runtime-prototype','flashable':False,'pending':['independent_bootstrap','boot_memory_reservation','full_combination_proofs'],
         'upstream_commit':chord['chord_keys_upstream_commit'],'requires':[],
         'writes':copy.deepcopy(chord['writes']),'symbols':copy.deepcopy(chord['symbols']),
         'parts':[{'dest':hex(start),'hex':raw.hex()}],
         'compressed_hex':packed.hex(),'raw_sha256':hashlib.sha256(raw).hexdigest(),
         'audit':{'own_bytes':used,'runtime_span':len(raw),'packed_bytes':len(packed),'reservations':reservations,'bank_hooks':0,'tg_hooks':0}}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--chord',required=True);p.add_argument('--bank',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 t=generate(json.loads(pathlib.Path(a.chord).read_text()),json.loads(pathlib.Path(a.bank).read_text()));text=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : réserves propres indépendantes',t['audit']['own_bytes'],'octets ; compressé',t['audit']['packed_bytes'],'; non flashable avant preuve bootstrap')
if __name__=='__main__':main()
