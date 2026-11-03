"""Retablir HALL350 a l'identique, en conservant gates et delai independants."""
from pathlib import Path
import hashlib,json,struct
BASE=0x46700000
def apply(meta,runtime,capture):
 capture=Path(capture);reference=(capture/'runtime.bin').read_bytes();eco=meta['eco_fx351'];hall=eco['previous_hall'];fs=meta['fx_menu']['symbols'];code=hall['code'];end=0x46704400
 old=bytes(runtime[code-BASE:code-BASE+eco['hall_bytes']]);assert hashlib.sha256(old).hexdigest()==eco['hall_sha256']
 original=reference[code-BASE:code-BASE+hall['code_bytes']];assert hashlib.sha256(original).hexdigest()==hall['sha256']
 patches=[]
 for at,size,expected in [(fs['fx_hall'],6,b'\x4e\xf9'+struct.pack('>I',eco['hall_symbols']['fx_hall'])),(fs['fx_rev_names']+44,4,struct.pack('>I',eco['hall_symbols']['eco_hall_name']))]:
  off=at-BASE;assert runtime[off:off+size]==expected
  new=reference[off:off+size];runtime[off:off+size]=new;patches.append(dict(at=at,old=expected.hex(),new=new.hex()))
 runtime[code-BASE:end-BASE]=reference[code-BASE:end-BASE]
 assert runtime[fs['fx_hall']-BASE:fs['fx_hall']-BASE+6]==b'\x4e\xf9'+struct.pack('>I',hall['symbols']['fx_hall'])
 name=int.from_bytes(runtime[fs['fx_rev_names']+44-BASE:fs['fx_rev_names']+48-BASE],'big');assert runtime[name-BASE:name-BASE+5]==b'HALL\0'
 eco['hall_restored']=True;eco['voice_first_pressure']=False;eco['native_tails_unchanged']=not eco.get('eco_delay');eco['quality_changed']=bool(eco.get('eco_delay'))
 return dict(code=code,code_bytes=hall['code_bytes'],sha256=hall['sha256'],patches=patches,HALL_matches350=True,Eco_HALL_removed=True,voice_and_filter_optimizations_retained=True,hardware_tested=False)
