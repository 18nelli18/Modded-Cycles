"""Art natif34x34 de Dummy et carte48x33, grilles originales monochromes."""
from pathlib import Path
import json,struct,sys,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import build_machine_identity_test as identity

def make(output,order):
 p=[[0]*34 for _ in range(34)]
 def dot(x,y,v=1):
  if 0<=x<34 and 0<=y<34:p[y][x]=v
 def line(x0,y0,x1,y1,v=1):
  dx=abs(x1-x0);sx=1 if x0<x1 else -1;dy=-abs(y1-y0);sy=1 if y0<y1 else -1;e=dx+dy
  while True:
   dot(x0,y0,v)
   if x0==x1 and y0==y1:break
   t=e*2
   if t>=dy:e+=dy;x0+=sx
   if t<=dx:e+=dx;y0+=sy
 # Cheveux plaques, oreilles, yeux, nez, joues et machoire articulee.
 for y,a,b in [(2,12,21),(3,10,23),(4,9,24),(5,8,25),(6,8,25),(7,8,25)]:
  for x in range(a,b+1):dot(x,y)
 line(9,8,9,19);line(24,8,24,19);line(9,7,15,6,0);line(17,7,23,5,0)
 line(7,12,7,17);line(6,13,6,16);line(8,12,8,17);line(25,12,26,12);line(26,12,27,13);line(27,13,27,16);line(26,17,25,17)
 for x in (11,19):
  line(x,9,x+3,8);line(x,11,x+3,11);line(x,14,x+3,14);line(x,11,x,14);line(x+3,11,x+3,14);dot(x+2,12);dot(x+2,13)
 line(16,12,15,17);line(15,17,18,17);dot(11,16);dot(22,16)
 line(10,19,23,19);line(11,20,22,20);line(11,18,11,23);line(22,18,22,23);line(11,23,22,23);line(13,24,20,24)
 for x in (13,16,19):dot(x,20,0)
 line(13,25,13,26);line(20,25,20,26)
 # Noeud papillon et revers de costume.
 line(16,27,12,25);line(12,25,12,29);line(12,29,16,27);line(17,27,21,25);line(21,25,21,29);line(21,29,17,27);dot(16,27);dot(17,27)
 line(11,26,6,29);line(6,29,4,33);line(22,26,27,29);line(27,29,29,33);line(10,28,14,33);line(23,28,19,33);line(16,29,16,33);line(17,29,17,33)
 profile=dict(machine=28,name='Dummy',icon='ventriloquist-dummy',**{'class':'NONE'},style='DUMMY',str=0,dex=0,mag=0)
 stats=identity.stats(profile);icon=identity.encode(p)
 def array(name,data):return 'const unsigned int '+name+'['+str(len(data)//4)+']={'+','.join(hex(v) for v in struct.unpack('>'+str(len(data)//4)+'I',data))+'};\n'
 text='typedef unsigned int u32;\nconst char dy_name[]="Dummy";\nconst unsigned char dy_order[]={'+','.join(map(str,order))+'};\nconst u32 dy_count='+str(len(order))+';\n'
 for label,w,h,data in [('stats',48,33,stats),('icon',34,34,icon)]:
  text+=array('dy_'+label+'_pixels',data)+array('dy_'+label+'_mask',identity.encode([[1]*w for _ in range(h)]))
  text+='const u32 dy_'+label+'_bitmap[7]={0x401117c8,'+str(w)+','+str(h)+',2,(u32)dy_'+label+'_pixels,(u32)dy_'+label+'_mask,0};\n'
 output.mkdir(parents=True,exist_ok=True);(output/'dummy-assets.c').write_text(text);(output/'dummy-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
 def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
 rows=b''.join(b'\0'+bytes(0 if p[y//4][x//4] else 255 for x in range(136)) for y in range(136))
 (output/'dummy-icon.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',136,136,8,0,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))
 return profile
