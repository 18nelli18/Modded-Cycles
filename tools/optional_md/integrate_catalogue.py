"""Tables28/181 et detours gardes, sur le socle Optional2.61 seulement."""
from pathlib import Path
import json,struct,sys,os
W=Path(os.environ['MD_WORK']);R=Path(__file__).resolve().parents[2];DEV=R
sys.path.insert(0,str(R/'tools'))
from mtlib import aplib
BASE=0x40000400;START=0x401aa140-BASE;RUN=0x46700000;TAIL=0x467ab360;DATA=0x4683c000;DESC=0x4683c800

def apply(image,module):
 meta=json.loads((R/'tools/machines/md/base-map.json').read_text());old=meta['tiny_extra']['symbols'];s=module['symbols'];end=int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 raw=image[START:end];rt,ops=aplib.depack(struct.pack('>II',len(raw),sum(raw)&0xffffffff)+raw)
 prefix=bytearray(image[:START]);rt=bytearray(rt);before=bytes(rt);tail=bytearray(image[end:]);edits=[]
 def area(at):return (prefix,BASE) if at<RUN else (rt,RUN) if at<TAIL else (tail,TAIL)
 def get(at,n):a,b=area(at);return bytes(a[at-b:at-b+n])
 def put(at,new):
  a,b=area(at);v=get(at,len(new));assert len(v)==len(new),(hex(at),len(new));a[at-b:at-b+len(new)]=new;edits.append(dict(at=at,old=v.hex(),new=new.hex()))
 def u32(at):return int.from_bytes(get(at,4),'big')
 def jump(at,to):put(at,b'\x4e\xf9'+struct.pack('>I',to))
 # Gardes de services Optional existantes : MIDI/WAVE/LEGACY restent masques.
 optional=json.loads((R/'docs/flasher-optional/recipe.js').read_text().split('=',1)[1].strip().rstrip(';'))
 for p in optional['patches']:
  expected=bytes.fromhex(p['old']);assert get(p['at'],len(expected))==expected,hex(p['at'])
  put(p['at'],bytes.fromhex(p['new']))
 edits=[]
 tables=[list(struct.unpack('>25I',get(DATA+100*k,100))) for k in range(4)]
 mapping=get(DATA+400,25);assert list(mapping)==list(range(25)),mapping
 moves={DATA+100:DATA+112,DATA+200:DATA+224,DATA+300:DATA+336,DATA+400:DATA+448}
 # References de code et des tables, exactement comme le generateur cumulatif.
 refs={hex(k):0 for k in moves}
 for a,b in ((prefix,BASE),(rt,RUN),(tail,TAIL)):
  for i in range(0,len(a)-3,2):
   v=int.from_bytes(a[i:i+4],'big')
   if v in moves:put(b+i,struct.pack('>I',moves[v]));refs[hex(v)]+=1
 assert all(refs.values()),refs
 spec=[('TrxB2','trx_b2_update',[('Distortion','DIST',0),('Dirt','DIRT',0),('Ramp','RAMP',96),('Hold','HOLD',64)],64),('TrxSD','trx_sd_update',[('Snap','SNAP',64),('Tone','TONE',64),('Bump','BUMP',0),('Bump Env','BENV',64)],32),('TrxCH','trx_ch_update',[('Metal','MTAL',64),('High Pass','HPF',64),('Resonance','RES',70),('Gap','GAP',32)],32)]
 cursor=DATA+0x400
 def string(v):
  nonlocal cursor
  raw=v.encode()+b'\0';at=cursor;assert not any(get(at,len(raw)));put(at,raw);cursor+=len(raw);return at
 desc=bytearray(get(DESC,166*56));template=get(DESC+131*56,280)
 for j,(name,update,knobs,decay) in enumerate(spec):
  tables[0].append(string(name));tables[1].append(s[update]);tables[2].append(s['md_render32']);tables[3].append(26+j)
  row=bytearray(template)
  for k,(long,short,default) in enumerate(knobs+[('Decay','DEC',decay)]):
   for off,value in ((8,0),(12,127<<8),(16,default<<8),(44,string(long)),(52,string(short))):struct.pack_into('>I',row,k*56+off,value)
  desc+=row
 assert cursor<=DESC and len(desc)==181*56 and DESC+len(desc)<=0x4683f000
 assert int.from_bytes(desc[41*56+12:41*56+16],'big')==24<<8
 struct.pack_into('>I',desc,41*56+12,27<<8);put(DESC,desc)
 for k,t in enumerate(tables):put(DATA+112*k,struct.pack('>28I',*t))
 put(DATA+448,mapping+bytes([25,26,27]))
 # Les helpers PUNCH propres restent en place ; leur map_state sera elargi.
 for name in ('map_state','shown','record_at','record_of','knob_vec','desc_machine','builder_row','lfo_gate'):jump(old[name],s[name])
 for side in ('left','right'):jump(old['tiny_'+side],s['md_identity_'+side])
 jump(old['tiny_menu_increment'],s['md_increment']);jump(0x400148aa,s['md_increment'])
 jump(old['marks'],s['md_marks']);jump(meta['fx_menu']['symbols']['fx_machine_step'],s['md_fx_step'])
 jump(0x467886fa,s['md_dispatch'])
 for at,reg in ((0x400a7dba,0x72),(0x400a7df4,0x70),(0x400147a4,0x70),(0x400a25e0,0x70)):
  assert get(at,2)==bytes([reg,24]),(hex(at),get(at,2).hex());put(at,bytes([reg,27]))
 assert get(0x4005a2b8,4)==bytes.fromhex('48780320');put(0x4005a2b8,bytes.fromhex('48780380'))
 bounds=set()
 for site in meta['tiny_extra']['wide_bounds']:
  at=int(site,16);assert get(at,2)==b'\x4e\xf9';target=u32(at+2)
  if target in bounds:continue
  bounds.add(target);raw=get(target,6);value=int.from_bytes(raw[2:],'big');assert value in (165,166),(hex(at),raw.hex());put(target,raw[:2]+struct.pack('>I',value+15))
 ld=meta['ld_api']
 assert u32(ld+12)==166;put(ld+12,struct.pack('>I',181))
 packed=aplib.repack(bytes(rt),ops,bytes(a!=b for a,b in zip(rt,before)));assert aplib.depack(packed)[0]==rt
 struct.pack_into('>I',prefix,0x40195ad0-BASE,BASE+START+len(packed)-8)
 result=bytes(prefix)+packed[8:]+bytes(tail)
 (W/'probe/CATALOGUE.json').write_text(json.dumps(dict(machine_count=28,descriptor_count=181,new_ids=[25,26,27],menu_order=[*range(17),*range(18,28),17],reference_counts=refs,edits=edits,symbols=s),indent=2)+'\n')
 return bytearray(result)
