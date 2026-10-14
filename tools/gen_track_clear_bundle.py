#!/usr/bin/env python3
"""Intégrer les adapters clear/Undo A+B dans les neuf blocs MIDI déjà réservés.

--bank prototype-b.json --audio prototype-a.json --output bundle.json
Les recettes originales restent intactes. Aucun stockage projet réintroduit.
"""
import argparse,copy,hashlib,json,pathlib,struct
import aplib_cost,build

def generate(bank,audio,dynamic=False):
 t=copy.deepcopy(bank);s=t['symbols'];ap=t['append'];part=ap['parts'][0]
 assert 'b_clear_lfo_undo' in t
 if not dynamic:assert t['ram_only_rollback']
 assert len(ap['parts'])==1 and ap['compress']=='aplib'
 dest=int(part['dest'],16);raw=bytearray.fromhex(part['hex']);oldend=dest+len(raw)
 start=int(audio['raw']['dest'],16);code=bytes.fromhex(audio['raw']['hex'])
 assert hashlib.sha256(code).hexdigest()==audio['raw']['sha256']
 assert int(s['ML_BANK_END'],16)==oldend<=start
 if not dynamic:assert start==0x401ce400
 assert audio['imports']['A_audio_owner']==s['ml_audio_lfo_owner']
 assert start+len(code)==int(audio['symbols']['avcl_end'],16)
 raw+=bytes(start-oldend)+code;raw+=bytes((-len(raw))%16);end=dest+len(raw)
 assert end<=0x401cf750,'réservation RAM dépassée'
 at=int(s['ml_boot_skip'],16)-dest;old=b'\x20\x7c'+struct.pack('>I',oldend)
 assert raw[at:at+6]==old;raw[at:at+6]=b'\x20\x7c'+struct.pack('>I',end)
 if dynamic:
  blocks=max(t.get('cache_blocks',0),(end-int(s['ML_TG_START'],16)+16383)//16384)
  for at,val in [(0x400792f2,0x401eb750+20*blocks),(0x400792bc,0x401eb750+20*(blocks+1)+16)]:
   row=next(w for w in t['writes'] if build.BASE+w['off']==at);row['new']=struct.pack('>I',val).hex()
  t['cache_blocks']=blocks
 t['writes']+=copy.deepcopy(audio['writes']);t['symbols'].update(audio['symbols'])
 packed=aplib_cost.pack(bytes(raw),depth=512,lazy=True)
 margin=build.END_LIMIT-int(ap['at'],16)-len(packed);assert margin>=0,'flash pleine'
 part['hex']=raw.hex();ap['size']=len(raw);ap['compressed_hex']=packed.hex()
 s['ML_BANK_END']=hex(end);s['ML_BANK_SIZE']=hex(len(raw))
 meta=t.get('midi_payload_rebase',{});meta['raw_sha256']=hashlib.sha256(raw).hexdigest();meta['packed_sha256']=hashlib.sha256(packed).hexdigest()
 t['a_clear_lfo_undo']=dict(adapter_start=hex(start),adapter_end=audio['symbols']['avcl_end'],adapter_size=len(code),raw_end=hex(end),flash_margin=margin,imports=audio['imports'],hooks=audio['writes'])
 t['description'].append('Prototype clear/Undo A+B : séquence et deux LFO, sources propres ; RAM uniquement.')
 return t

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bank',required=True);p.add_argument('--audio',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');p.add_argument('--dynamic',action='store_true');a=p.parse_args()
 t=generate(json.loads(pathlib.Path(a.bank).read_text()),json.loads(pathlib.Path(a.audio).read_text()),a.dynamic);data=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==data
 else:out.write_text(data)
 print('ok : clear/Undo A+B intégré ; RAW',t['symbols']['ML_BANK_SIZE'],'; marge flash',t['a_clear_lfo_undo']['flash_margin'])
if __name__=='__main__':main()
