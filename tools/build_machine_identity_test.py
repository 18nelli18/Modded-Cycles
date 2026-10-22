"""Profils et initiales MACHINES prives sur la base exacte du principal 2.12.

Les bitmaps sont dessines depuis les grilles de ce fichier. Seuls trois points
du dessin UI et la taille du chargement changent ; audio et sections hors MAIN
restent identiques. Aucun fichier du site public n'est ecrit.
"""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
from mtlib import aplib,container
from mtlib.syx import unwrap,wrap,BYTES_PER_MSG
import aplib_grow

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/firmware'
BASE=0x40000400;START=0x401aa140-BASE;TAIL=0x467ab360;ORIGIN=0x467c2000
SOURCE_SHA='5111c5401520856496c9626598b6a10c4929e123052d512cc5384621b8ca73ab'
SOURCE=ROOT/'tools/machines/machine_identity'
# Petites lettres de trois pixels, comme les etiquettes des cartes natives.
FONT={
 'A':['010','101','111','101','101'],'B':['110','101','110','101','110'],
 'C':['011','100','100','100','011'],'D':['110','101','101','101','110'],
 'E':['111','100','110','100','111'],'F':['111','100','110','100','100'],
 'G':['011','100','101','101','011'],'H':['101','101','111','101','101'],
 'I':['111','010','010','010','111'],'J':['001','001','001','101','010'],
 'K':['101','101','110','101','101'],'L':['100','100','100','100','111'],
 'M':['101','111','111','101','101'],'N':['101','111','111','111','101'],
 'O':['010','101','101','101','010'],'P':['110','101','110','100','100'],
 'Q':['010','101','101','111','011'],'R':['110','101','110','101','101'],
 'S':['011','100','010','001','110'],'T':['111','010','010','010','010'],
 'U':['101','101','101','101','111'],'V':['101','101','101','101','010'],
 'W':['101','101','111','111','101'],'X':['101','101','010','101','101'],
 'Y':['101','101','010','010','010'],'Z':['111','001','010','100','111'],
 ':':['0','1','0','1','0']}
# Silhouettes anguleuses pour les monogrammes, sans image tierce embarquee.
ICONS={
 'A':['01110','11011','11011','11111','11011','11011','11011'],
 'B':['11110','11011','11011','11110','11011','11011','11110'],
 'C':['01111','11000','11000','11000','11000','11000','01111'],
 'D':['11110','11011','11011','11011','11011','11011','11110'],
 'M':['10001','11011','11111','11111','11011','11011','11011'],
 'O':['01110','11011','11011','11011','11011','11011','01110'],
 'P':['11110','11011','11011','11110','11000','11000','11000'],
 'R':['11110','11011','11011','11110','11100','11010','11011'],
 'S':['01111','11000','11000','01110','00011','00011','11110'],
 'T':['11111','11111','00110','00110','00110','00110','00110'],
 'V':['11011','11011','11011','11011','11011','01010','00100'],
 'W':['11011','11011','11011','11111','11111','11011','10001'],
 'Y':['11011','11011','01010','00100','00100','00100','00100']}

def encode(pixels):
 h=len(pixels);w=len(pixels[0]);stride=(h+31)//32;out=bytearray(w*stride*4)
 for y,row in enumerate(pixels):
  for x,on in enumerate(row):
   if on:
    yy=h-1-y;off=(x*stride+yy//32)*4
    struct.pack_into('>I',out,off,struct.unpack_from('>I',out,off)[0]|1<<(31-yy%32))
 return bytes(out)

def stats(profile):
 p=[[0]*48 for _ in range(33)]
 def text(s,y):
  x=0
  for ch in s:
   glyph=FONT[ch]
   for dy,line in enumerate(glyph):
    for dx,c in enumerate(line):p[y+dy][x+dx]=int(c)
   x+=4
 for label,y,value in [('STR',14,profile['str']),('DEX',21,profile['dex']),('MAG',28,profile['mag'])]:
  text(label+':',y)
  for i in range(5):
   shape=['00100','01110','11111','01110','00100'] if i<value else ['00100','01010','10001','01010','00100']
   for dy,line in enumerate(shape):
    for dx,c in enumerate(line):p[y+dy][16+i*6+dx]=int(c)
 if profile['machine']!=6:text('CLASS:'+profile['class'],0);text('STYLE:'+profile['style'],7)
 return encode(p)

def icon(profile):
 # Entree reservee, jamais dessinee : Wizard garde son Bitmap chapeau natif.
 if profile['icon']=='hat':return encode([[0]*34 for _ in range(34)])
 s=profile['icon'];sx,sy=(4,4) if len(s)==1 else (2,3)
 width=len(s)*5*sx+(len(s)-1)*2;height=7*sy
 x0=(34-width-4)//2;y0=(34-height)//2
 p=[[0]*34 for _ in range(34)]
 for i,ch in enumerate(s):
  for y,line in enumerate(ICONS[ch]):
   for x,c in enumerate(line):
    if c=='0':continue
    for dy in range(sy):
     yy=y0+y*sy+dy;skew=(height-1-(y*sy+dy))//7
     for dx in range(sx):
      xx=x0+i*(5*sx+2)+x*sx+dx+skew
      assert 0<=xx<34 and 0<=yy<34
      p[yy][xx]=1
 return encode(p)

def read(path):
 stream,info=unwrap(path.read_bytes());pkg=container.parse(stream)
 section=next(s for s in pkg['sections'] if s['id']==3)
 image,ops=aplib.depack(pkg['blob'][section['off']:section['off']+section['size']])
 return info,pkg,image,ops

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--no-filter',action='store_true');args=parser.parse_args()
 source=OUT/('no-filter-dx-toggle-test-v14.syx' if args.no_filter else 'all-features-dx-ltc-main-212.syx')
 expected='31f7f66a8b5a8b3dcfd82f20135f66f156eb3f2ec863cb6ed4faeedc6abd367a' if args.no_filter else SOURCE_SHA
 assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
 meta=json.loads(source.with_suffix('.json').read_text())
 assert meta['sha256']==expected
 assert meta['filter']==(not args.no_filter)
 profiles=json.loads((SOURCE/'profiles.json').read_text())
 assert [p['machine'] for p in profiles]==list(range(6,18))
 assert len({(p['str'],p['dex'],p['mag']) for p in profiles})==12
 assert len({p['icon'] for p in profiles})==12
 cross=str(ROOT.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 # Adresses separees pour que les detours ne dependent pas de la taille des images.
 stats_at=ORIGIN+0x400;icons_at=stats_at+12*28;data_at=(icons_at+12*28+3)&~3
 obj=OUT/'identity.o';elf=OUT/'identity.elf';binary=OUT/'identity.bin';ld=OUT/'identity.ld'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(SOURCE/'identity.S'),'-o',str(obj)],check=True)
 ld.write_text(f'SECTIONS {{ .text {ORIGIN:#x} : {{ *(.text*) }} }}\nPROVIDE(identity_stats = {stats_at:#x});\nPROVIDE(identity_icons = {icons_at:#x});\n')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
 symbols={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(r.split())==3}
 code=binary.read_bytes();assert len(code)<0x400
 payload=bytearray(code.ljust(data_at-ORIGIN,b'\0'))
 for table,make,w,h in [(stats_at,stats,48,33),(icons_at,icon,34,34)]:
  mask_at=ORIGIN+len(payload);payload.extend(encode([[1]*w for _ in range(h)]))
  for i,p in enumerate(profiles):
   at=ORIGIN+len(payload);payload.extend(make(p))
   struct.pack_into('>7I',payload,table-ORIGIN+28*i,0x401117c8,w,h,2,at,mask_at,0)
 info,pkg,image,_=read(source);prefix=bytearray(image[:START])
 tail_start=int.from_bytes(prefix[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 packed=image[START:tail_start]
 runtime,runtime_ops=aplib.depack(struct.pack('>II',len(packed),sum(packed)&0xffffffff)+packed)
 runtime=bytearray(runtime);original_runtime=bytes(runtime);tail=bytearray(image[tail_start:])
 assert len(tail)+TAIL<ORIGIN
 edits=[]
 def patch(at,old,new):
  area,off=(runtime,at-0x46700000) if at<TAIL else (tail,at-TAIL)
  assert area[off:off+len(old)]==old,(hex(at),area[off:off+len(old)].hex())
  assert len(old)==len(new);area[off:off+len(new)]=new;edits.append({'at':hex(at),'old':old.hex(),'new':new.hex()})
 jump=lambda at:b'\x4e\xf9'+struct.pack('>I',at)
 if args.no_filter:
  # Le v14 sans filtre precede les deux abreviations approuvees en 2.12.
  patch(0x467afb53,b'Silent\0',b'SIL\0\0\0\0')
  patch(0x467afb65,b'Latch\0',b'LTC\0\0\0')
 patch(0x46788124,bytes.fromhex('227940fe32cc'),jump(symbols['identity_left']))
 patch(0x4678813e,bytes.fromhex('d8b940fe384c'),jump(symbols['identity_right']))
 patch(0x467b668c,bytes.fromhex('0c8300000006'),jump(symbols['identity_wizard']))
 tail.extend(bytes(ORIGIN-TAIL-len(tail)));tail.extend(payload)
 assert TAIL+len(tail)<0x46800000
 # Seules les deux instructions UI declarees different du runtime de reference.
 changed={i for i,(a,b) in enumerate(zip(runtime,original_runtime)) if a!=b}
 allowed={at-0x46700000+i for at in [0x46788124,0x4678813e] for i in range(6)}
 assert changed<=allowed
 stream=aplib.repack(bytes(runtime),runtime_ops,bytes(a!=b for a,b in zip(runtime,original_runtime)))
 assert aplib.depack(stream)[0]==bytes(runtime)
 struct.pack_into('>I',prefix,0x40195ad0-BASE,BASE+START+len(stream)-8)
 struct.pack_into('>I',prefix,0x40195ad8-BASE,len(tail))
 data=bytes(prefix)+stream[8:]+bytes(tail)
 official=ROOT/'firmware/model-cycles_OS1.13.syx';oi,op,stock,ops=read(official)
 device=json.loads((ROOT/'tweaks/model-cycles_OS1.13/device.json').read_text())
 assert hashlib.sha256(official.read_bytes()).hexdigest()==device['stock_syx_sha256']
 dirty=bytearray(len(data));dirty[:START]=bytes(a!=b for a,b in zip(data[:START],stock[:START]));dirty[START:]=b'\1'*(len(data)-START)
 section=aplib_grow.repack_grow(bytes(data),ops,dirty,START);assert aplib.depack(section)[0]==bytes(data)
 plains=[]
 for s in op['sections']:
  try:plains.append(aplib.depack(op['blob'][s['off']:s['off']+s['size']])[0])
  except Exception:pass
 key=container.find_key(plains,op['blob'][:-container.DIGEST_LEN],op['blob'][-container.DIGEST_LEN:]);assert key
 rebuilt=container.rebuild(op,{3:section},key)
 raw=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),oi['product'],oi['start_seq'])
 dest=OUT/('no-filter-machine-identity-test-v15.syx' if args.no_filter else 'all-features-machine-identity-test-v15.syx');dest.write_bytes(raw)
 _,final,after,_=read(dest);assert after==bytes(data)
 for s in op['sections']:
  if s['id']==3:continue
  t=next(t for t in final['sections'] if t['id']==s['id'])
  assert op['blob'][s['off']:s['off']+s['size']]==final['blob'][t['off']:t['off']+t['size']]
 meta.update(base=source.name,base_sha256=expected,sha256=hashlib.sha256(raw).hexdigest(),main_os_sha256=hashlib.sha256(data).hexdigest(),hardware_tested=False,release=None,machine_identities=profiles,identity_symbols=symbols,identity_ui_edits=edits,identity_stats=stats_at,identity_icons=icons_at,identity_end=ORIGIN+len(payload),runtime_tail_end=hex(ORIGIN+len(payload)),stock_hat_preserved=True,main_changed=False,mute_latch_label='LTC',silent_label='SIL')
 dest.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
 print('BUILT private v15',meta['sha256'],'payload bytes',len(payload),'three UI edits; stock hat and audio code unchanged',flush=True)

if __name__=='__main__':main()
