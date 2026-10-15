"""Illustration propre 1 bit : chapeau droit et vraies étoiles à cinq branches.

Le dessinateur natif compte Y vers le haut ; le dessin ci-dessous est décrit
vers le bas puis inversé lors de l'encodage, sans changer les tailles du slot.
"""
from pathlib import Path
import math,struct
P=Path('work/sample-wizard-main/src/sampler_icons')
def inside(x,y,poly):
 odd=False
 for i,(a,b) in enumerate(poly):
  c,d=poly[i-1]
  if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:odd=not odd
 return odd

def star(cx,cy,r):
 return [(cx+math.cos(-math.pi/2+i*math.pi/5)*(r if i%2==0 else r*.40),cy+math.sin(-math.pi/2+i*math.pi/5)*(r if i%2==0 else r*.40)) for i in range(10)]
cone=[(13,25),(17,20),(17,15),(19,10),(23,6),(29,1),(27,8),(26,13),(28,19),(33,25)]
band=[(16,20),(28,19),(30,22),(14,23)]
stars=[star(6.5,10.5,5.5),star(41.5,12.5,5.5),star(37.5,3.5,3.5)]
cutout=star(22.5,14.5,5.2)
for name,w,h in [('A_48x33',48,33),('B_34x34',34,34)]:
 raw=bytearray(w*8)
 for yy in range(h):
  for xx in range(w):
   x,y=(xx+.5)*48/w,(yy+.5)*33/h
   hat=inside(x,y,cone) or ((x-24)/20)**2+((y-27)/3.6)**2<=1
   if inside(x,y,band) or inside(x,y,cutout):hat=False
   if hat or any(inside(x,y,p) for p in stars):
    ny=h-1-yy;at=xx*8+(ny//32)*4;word=struct.unpack_from('>I',raw,at)[0]|(1<<(31-ny%32));struct.pack_into('>I',raw,at,word)
 (P/('sampler_icon_'+name+'.bin')).write_bytes(raw)
print('PASS deux bitmaps propres, chapeau droit et étoiles à cinq branches ; 384/272 octets inchangés.')
