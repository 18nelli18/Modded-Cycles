"""Restaurer les deux labels vivants de CTRL-ALL, retires a tort du payload."""
import hashlib,struct
BASE=0x46700000
def apply(meta,runtime):
 owner=meta['control_all_latch'];start=owner['code'];end=start+owner['code_bytes']
 assert start in (0x4691f100,0x4692a000) and owner['code_bytes']==1368
 at=start+0x53c;raw=b'CTRL-ALL OFF\0CTRL-ALL ON\0'
 assert not any(runtime[at-BASE:at-BASE+len(raw)])
 code=bytes(runtime[start-BASE:at-BASE])
 assert code.count(struct.pack('>I',at))>=1 and code.count(struct.pack('>I',at+13))>=1
 runtime[at-BASE:at-BASE+len(raw)]=raw
 return dict(patches=[dict(region='runtime',at=at,old=bytes(len(raw)).hex(),new=raw.hex())],bytes=len(raw),code_changed=False,audio_hooks_changed=False,labels=['CTRL-ALL OFF','CTRL-ALL ON'],sha256=hashlib.sha256(raw).hexdigest(),hardware_tested=False)
