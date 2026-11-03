"""Remplacer le cache48k valide par le partage complet des coefficients."""
import hashlib
from filter_div307 import apply as compile_filter,CODE,END

def apply(meta,runtime,out):
 base=0x46700000;previous=meta['filter_single_div']
 assert meta.get('filter_restore_48k') and not meta.get('filter_half_rate')
 blob=bytes(runtime[CODE-base:CODE-base+previous['code_bytes']])
 assert hashlib.sha256(blob).hexdigest()==previous['sha256']
 for patch in previous['patches']:
  at=patch['at']-base;assert runtime[at:at+6]==bytes.fromhex(patch['new'])
  runtime[at:at+6]=bytes.fromhex(patch['old'])
 runtime[CODE-base:END-base]=bytes(END-CODE)
 result=compile_filter(meta,runtime,out,full_cache=True)
 result['previous_sha256']=previous['sha256']
 return result
