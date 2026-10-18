#!/usr/bin/env python3
"""Toutes les selections TINY/RETROSYN : vrai constructeur OS, tables et callbacks."""
import json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import build,syntakt,gen_sdvintage_7th as g7,test_sdvintage_7th as T,mcengine as E
ROOT=HERE.parent.parent

def main():
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));st=syntakt.dsp_image(str(ROOT/'firmware/Syntakt_OS1.42.syx'));pay=0x46700000
 class UI(T.UI):
  def __init__(self,img,payload=b''):
   super().__init__(img,payload);self.uc.mem_map(pay,0x100000);self.uc.mem_write(pay,payload)
 paths=sorted((ROOT/'build/machine-combinations').glob('[0-9]*-[wn].json'));assert len(paths)==1536
 for number,p in enumerate(paths):
  entry=json.loads(p.read_text(encoding='utf-8'));e=entry['engine'];wizard='wizard' in entry;first=7 if wizard else 6;names=e['machine_names'];mask=e['machine_selection']
  expected=['Kick','Snare','Metal','Perc','Tone','Chord']+(['Sampler'] if wizard else [])+[n for bit,n in [(1,'SDVtg'),(2,'CPVtg'),(4,'SYToy'),(8,'SYBit'),(16,'SYSwm'),(32,'MACRO'),(64,'ACID'),(128,'Wave'),(256,'TINY'),(512,'RETROSYN')] if mask&bit]
  assert names==expected,(p,names,expected)
  recipes=([entry['wizard']] if wizard else [])+[e];img,_=build.apply_writes(stock,recipes);runtime=build.payload_runtime(e,stock,st)
  u=UI(img,runtime);u.call(0x4005a274);assert u.u32(T.ROW_COUNT)==len(names),(p,u.u32(T.ROW_COUNT))
  for index in range(first,len(names)):
   assert u.call(0x4005a692,12,index)==77+5*(index-first),(p,index)
   at=int(e['machine_tables'],16)-pay+4*index;address=int.from_bytes(runtime[at:at+4],'big')-pay
   name=runtime[address:runtime.index(b'\0',address)].decode('ascii');assert name==names[index],(p,index,name)
   for offset in (4*len(names),8*len(names)):
    callback=int.from_bytes(runtime[at+offset:at+offset+4],'big');assert pay<=callback<pay+len(runtime),(p,index,hex(callback))
  if mask&128:
   ui=next(bytes.fromhex(x['hex']) for x in e['append']['parts'] if x['dest']=='0x4677a580')
   assert ui[0x35]==first+(mask&31).bit_count()+bool(mask&32)+bool(mask&64),(p,ui[0x35])
  assert not u.bad,(p,u.bad)
  if not mask&31:assert 'syntakt' not in e['append'] and not any('syntakt' in x for x in e['append']['parts'])
  if number%64==63:print('PASS',number+1,'/1536 menus, descripteurs, noms, callbacks et choix sans fichier Syntakt',flush=True)
 print('PASS toutes les 1536 selections, avec/sans Wizard, aucun ajout impose',flush=True)
if __name__=='__main__':main()
