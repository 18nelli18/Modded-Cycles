"""Note133 : candidat filtre DX approuve, valeurs raccourcies en LTC et SIL.

Reconstruit le conteneur officiel, conserve les sections autres que MAIN.
Usage : python tools/build_dx_main_release.py
"""
import hashlib,json,struct
from pathlib import Path
from mtlib import aplib,container
from mtlib.syx import unwrap,wrap,BYTES_PER_MSG
import aplib_grow

ROOT=Path(__file__).resolve().parents[1]
BASE=0x40000400
START=0x401aa140-BASE
TAIL=0x467ab360
SOURCE_SHA='dc4de4c7b75affc7002f70d023ca131ff370b679b2b10c8662ab3c8959963f1d'

def read(path):
 stream,info=unwrap(path.read_bytes());pkg=container.parse(stream)
 section=next(s for s in pkg['sections'] if s['id']==3)
 image,ops=aplib.depack(pkg['blob'][section['off']:section['off']+section['size']])
 return info,pkg,image,ops

def main():
 source=ROOT/'output/firmware/all-features-dx-toggle-test-v14.syx'
 official=ROOT/'firmware/model-cycles_OS1.13.syx'
 assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA
 device=json.loads((ROOT/'tweaks/model-cycles_OS1.13/device.json').read_text())
 assert hashlib.sha256(official.read_bytes()).hexdigest()==device['stock_syx_sha256']
 _,before,image,_=read(source)
 info,pkg,stock,ops=read(official)
 data=bytearray(image)
 tail_start=int.from_bytes(data[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 label_offset=tail_start+0x467afb65-TAIL
 assert data[label_offset:label_offset+6]==b'Latch\0'
 data[label_offset:label_offset+6]=b'LTC\0\0\0'
 silent_offset=tail_start+0x467afb53-TAIL
 assert data[silent_offset:silent_offset+7]==b'Silent\0'
 data[silent_offset:silent_offset+7]=b'SIL\0\0\0\0'
 changed=[i for i,(a,b) in enumerate(zip(image,data)) if a!=b]
 assert changed==[silent_offset+i for i in range(1,6)]+[label_offset+i for i in range(1,5)]
 dirty=bytearray(len(data));dirty[:START]=bytes(a!=b for a,b in zip(data[:START],stock[:START]));dirty[START:]=b'\1'*(len(data)-START)
 section=aplib_grow.repack_grow(bytes(data),ops,dirty,START)
 assert aplib.depack(section)[0]==bytes(data)
 plains=[]
 for sec in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-container.DIGEST_LEN],pkg['blob'][-container.DIGEST_LEN:]);assert key
 rebuilt=container.rebuild(pkg,{3:section},key)
 raw=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq'])
 dest=ROOT/'output/firmware/all-features-dx-ltc-main-212.syx';dest.write_bytes(raw)
 _,result,after,_=read(dest);assert after==bytes(data)
 for sec in pkg['sections']:
  if sec['id']==3:continue
  other=next(s for s in result['sections'] if s['id']==sec['id'])
  assert pkg['blob'][sec['off']:sec['off']+sec['size']]==result['blob'][other['off']:other['off']+other['size']]
 meta=json.loads(source.with_suffix('.json').read_text())
 meta.update(base=source.name,base_sha256=SOURCE_SHA,sha256=hashlib.sha256(raw).hexdigest(),main_os_sha256=hashlib.sha256(after).hexdigest(),release='2.12',mute_latch_label='LTC',silent_label='SIL',label_only_change=True,diagnostics='toggle',dx_default=False,hardware_tested=False,release_approved_by='AveyCole')
 dest.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
 print('PASS only nine label bytes changed; other sections exact; DX Off preserved',meta['sha256'],meta['main_os_sha256'],flush=True)

if __name__=='__main__':main()
