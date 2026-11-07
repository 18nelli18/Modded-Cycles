"""Restaure les textes partages des sept delays apres le retrait du telephone."""
import struct
BASE=0x46700000
LABELS={0:'DELAY',1:'CRUSH 1',2:'CRUSH 2',5:'PING PONG',9:'DUB',10:'DUCK',11:'PHASER'}
def apply(meta,runtime):
 assert meta.get('remove_delay384') and not meta.get('delay_labels386')
 at=meta['per_track_fx']['symbols']['pots_del_names'];ptr=struct.unpack_from('>13I',runtime,at-BASE);patches=[]
 for index,label in LABELS.items():
  target=ptr[index];raw=label.encode()+b'\0';off=target-BASE;old=bytes(runtime[off:off+len(raw)]);assert old==bytes(len(raw)),(index,old)
  runtime[off:off+len(raw)]=raw;patches.append(dict(at=target,old=old.hex(),new=raw.hex()))
 return dict(shared_delay_labels_restored=True,labels=LABELS,patches=patches,hardware_tested=False)
