"""Versionner le titre d'une livraison signee sans modifier son audio/runtime."""
from pathlib import Path
import argparse,json,hashlib,os,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mtlib import aplib,container
from mtlib.syx import unwrap,wrap,BYTES_PER_MSG
from title204_assets import apply
from gen_governor_recovery_test import BASE

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('source','metadata','output','development-root'):p.add_argument('--'+name,required=True,type=Path)
 p.add_argument('--version',required=True);p.add_argument('--edition',choices=('full','lite'),required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 m=json.loads(a.metadata.read_text());raw=a.source.read_bytes();sha=lambda x:hashlib.sha256(x).hexdigest()
 assert sha(raw)==m['sha256']
 stream,info=unwrap(raw);pkg=container.parse(stream);sec=next(s for s in pkg['sections'] if s['id']==3)
 original,ops=aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']]);image=bytearray(original)
 cross=a.development_root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin';os.environ['PATH']=str(cross)+os.pathsep+os.environ.get('PATH','')
 edits=[]
 def patch(at,old,new,prefix):
  off=at-BASE;assert bytes(prefix[off:off+len(old)])==old
  assert len(new)<=len(old),'Le nouveau titre ne doit pas deborder'
  prefix[off:off+len(new)]=new;edits.append(dict(at=at,size=len(new)))
 title=apply(a.development_root,a.output,image,patch,a.version,lite=a.edition=='lite',previous=m['title_screen'])
 dirty=bytes(x!=y for x,y in zip(image,original));assert len(image)==len(original)
 assert sum(dirty)>0
 for i,v in enumerate(dirty):
  if v:assert title['code']-BASE<=i<title['code']-BASE+title['code_bytes']
 packed=aplib.repack(bytes(image),ops,dirty)
 from bootstrap205_assets import pack as safe_pack
 packed,packing=safe_pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
 plains=[]
 for s in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][s['off']:s['off']+s['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key
 rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
 result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq'])
 after=container.parse(unwrap(result)[0])
 for old,new in zip(pkg['sections'],after['sections']):
  if old['id']!=3:assert pkg['blob'][old['off']:old['off']+old['size']]==after['blob'][new['off']:new['off']+new['size']]
 name='Supermodel_'+('Lite_' if a.edition=='lite' else '')+a.version+'_'+sha(result)[:12]+'.syx'
 (a.output/name).write_bytes(result)
 m.update(sha256=sha(result),main_os_sha256=sha(image),release=a.version,title_screen=title,hardware_tested=False)
 if 'per_track_fx' in m:m['per_track_fx'].update(sha256=sha(result),main_sha256=sha(image),flash_bytes=len(rebuilt),syx_bytes=len(result))
 (a.output/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n')
 proof=dict(source_sha256=sha(raw),sha256=sha(result),version=a.version,title=title,only_startup_code_changed=True,changed_main_bytes=sum(dirty),recovery_updater_unchanged=True,flash_bytes=len(rebuilt),packing=packing,hardware_tested=False)
 (a.output/'TITLE-PROOF.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
if __name__=='__main__':main()
