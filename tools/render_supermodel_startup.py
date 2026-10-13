#!/usr/bin/env python3
"""Rendu des pixels propres transmis par l'émulation, sans modifier d'image source."""
import argparse,json
from PIL import Image
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--frames',required=True);ap.add_argument('--gif');ap.add_argument('--png');a=ap.parse_args()
frames=json.load(open(a.frames));on,off=(31,36,87),(178,182,226)
pics=[]
for frame in frames:
 im=Image.new('RGB',(128,64));im.putdata([on if v else off for row in frame for v in row]);pics.append(im.resize((768,384),Image.Resampling.NEAREST))
if a.gif:pics[0].save(a.gif,save_all=True,append_images=pics[1:],duration=[20]*79+[200],loop=0)
if a.png:pics[-1].save(a.png)
