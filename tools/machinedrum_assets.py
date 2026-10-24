"""Assets prives MD TRX-BD depuis l'image utilisateur et ses tables de boot.
Aucun octet ROM genere n'est destine au depot. Note136.
"""
import hashlib,json,struct
from pathlib import Path
SHA='68542e30917b9918ccaee2b2237df62c8a00479938680b85aca93ce4fbca44c8'
def prepare(root,build):
 firmware=root/'firmware/elektron_sps1-1uw_os1.63.bin';assert hashlib.sha256(firmware.read_bytes()).hexdigest()==SHA
 ref=root/'output/firmware/machinedrum-audit';meta=json.loads((ref/'reference.json').read_text());assert meta['firmware_sha256']==SHA
 sine=ref/'sine.bin';assert hashlib.sha256(sine.read_bytes()).hexdigest()==next(x['sha256'] for x in meta['dumps'] if x['file']=='sine.bin')
 main=(root/'output/firmware/machinedrum-reference/mainos.bin').read_bytes();manifest=json.loads((root/'output/firmware/machinedrum-reference/manifest.json').read_text());assert hashlib.sha256(main).hexdigest()==next(x['sha256'] for x in manifest['blobs'] if x['name']=='MainOS')
 def convert(file):
  data=file.read_bytes();return b''.join(struct.pack('>i',(int.from_bytes(data[i:i+3],'little')^0x800000)-0x800000) for i in range(0,len(data),3))
 data={'md_sine':convert(sine),'md_attack':convert(ref/'bd-attacks.bin'),'md_pitch':main[0x4bd94:0x4bf94],'md_decay':main[0x4bf94:0x4c794]}
 text='.section .rodata\n.balign 4\n'
 for name,blob in data.items():
  path=build/(name+'.bin');path.write_bytes(blob);text+=f'.globl {name}\n{name}:\n.incbin "{path.as_posix()}"\n.balign 4\n'
 source=build/'md-data.S';source.write_text(text);return source
