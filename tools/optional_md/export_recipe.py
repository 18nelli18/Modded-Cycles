"""Recette navigateur sans tables ROM ni descripteurs natifs copies."""
from pathlib import Path
import sys,json,hashlib,struct,os
W=Path(os.environ['MD_WORK']);R=Path(__file__).resolve().parents[2];S=R/'tools/machines/md'
sys.path[:0]=[str(S),str(R/'tools')]
import headers
from mtlib import aplib,container
from mtlib.syx import unwrap
from title204_assets import apply as title_apply
load=lambda p:json.loads(p.read_text())
m=load(W/'probe/BUILD.json');cat=load(W/'probe/CATALOGUE.json');budget=load(W/'probe/SPARSE-BUDGET.json');sy=m['symbols'];blob=bytearray((W/'probe/md.bin').read_bytes());filled_hash=hashlib.sha256(blob).hexdigest()
parts=[]
for name,(symbol,n) in headers.ARRAYS.items():
 off=sy[symbol]-m['code'];assert off>=0 and off+4*n<=len(blob)
 parts.append(dict(name=name,offset=off,size=4*n));blob[off:off+4*n]=bytes(4*n)
sine=sy['trx_b2_sine']-m['code'];body=blob[:sine];suffix=blob[sine+131072:]
excluded={0x4683c000,0x4683c070,0x4683c0e0,0x4683c150,0x4683c1c0,0x4683c800}
patches=[p for p in cat['edits'] if p['at'] not in excluded]
desc=bytes.fromhex(next(p['new'] for p in cat['edits'] if p['at']==0x4683c800));names=bytes.fromhex(next(p['new'] for p in cat['edits'] if p['at']==0x4683c000))
machines=[]
for j,name in enumerate(('TrxB2','TrxSD','TrxCH')):
 fields=[]
 for k in range(5):fields.append({str(off):int.from_bytes(desc[(166+j*5+k)*56+off:(166+j*5+k)*56+off+4],'big') for off in (8,12,16,44,52)})
 machines.append(dict(id=25+j,name=name,name_pointer=int.from_bytes(names[4*(25+j):4*(26+j)],'big'),update=sy[['trx_b2_update','trx_sd_update','trx_ch_update'][j]],render=sy['md_render32'],descriptor_fields=fields))
loader=(W/'probe/load.bin').read_bytes();fixups={}
for name,value in [('source',budget['source']),('deltas',budget['source']+len(body)+len(suffix))]:
 needle=struct.pack('>I',value);offsets=[i for i in range(0,len(loader)-3,2) if loader[i:i+4]==needle];assert len(offsets)==1,(name,offsets);fixups[name]=offsets[0]
base_map=load(R/'tools/machines/md/base-map.json');title=base_map['target_title'];title_edits=base_map['title_edits']
recipe=dict(source_sha256=budget['source_sha256'],release='2.62',status='experimental',hardware_tested=False,upstream='Talachan12/Elektron-Model-Machinedrum',revision='70e1483535c5a6919ff170ce3b79ba4a10c066ac',code=m['code'],code_bytes=m['code_bytes'],bss=m['bss'],bss_bytes=m['bss_bytes'],symbols=sy,module_body=body.hex(),module_suffix=suffix.hex(),sine_offset=sine,parts=parts,filled_module_sha256=filled_hash,patches=patches,machines=machines,loader=loader.hex(),loader_reserve=192,loader_fixups=fixups,title=title,title_edits=title_edits,full_mask=0x3fffff,md_bits=0x380000,MD_SYX_sha256='a58cd61f2efacfb07add0c643162fb4365c30e73831f2021c17b4aa3b42cabd5',MD_BIN_sha256='68542e30917b9918ccaee2b2237df62c8a00479938680b85aca93ce4fbca44c8')
p=W/'machinedrum-data.js';p.write_text('window.MCOptionalMDData='+json.dumps(recipe,separators=(',',':'))+';\n')
(W/'probe/BROWSER-RECIPE.json').write_text(json.dumps(recipe,indent=2)+'\n')
print('Exported browser recipe:',p.stat().st_size,'bytes; all MD arrays zeroed, descriptors cloned at build time')
