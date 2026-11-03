"""Comparaison privee : restaure le LOW48k de311 sans toucher au sommeil313."""
from pathlib import Path
import hashlib,json

def apply(meta,runtime,capture):
    capture=Path(capture); donor=capture.parents[2]/'main/full/BUILD.json'
    # La capture froide et ses metadonnees doivent designer le meme prototype.
    source=json.loads(donor.read_text()); proof=json.loads((capture/'capture.json').read_text())
    assert proof['source']==source['sha256'] and 'filter_half_rate' not in source
    old=meta['filter_half_rate']; base=0x46700000
    raw=(capture/'runtime.bin').read_bytes(); changes=[]
    def restore(at,size):
        before=bytes(runtime[at-base:at-base+size]); after=raw[at-base:at-base+size]
        runtime[at-base:at-base+size]=after
        changes.append(dict(at=at,bytes=size,before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest()))
    for p in old['patches']:
        at=p['at']; assert bytes(runtime[at-base:at-base+6]).hex()==p['new']
        assert raw[at-base:at-base+6].hex()==p['old']
        restore(at,6)
    restore(old['code'],old['code_bytes'])
    restore(old['coeff'],0x46705858-old['coeff'])
    coeff=source['filter_single_div']; assert hashlib.sha256(raw[coeff['code']-base:coeff['code']-base+coeff['code_bytes']]).hexdigest()==coeff['sha256']
    meta['filter_single_div']=coeff
    del meta['filter_half_rate']
    return dict(rate=48000,source_sha256=source['sha256'],changes=changes,idle_sleep_unchanged=True,hardware_tested=False)
