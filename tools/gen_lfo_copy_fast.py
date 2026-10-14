#!/usr/bin/env python3
"""LFO2 : copies ColdFire mémoire→mémoire, sans changer son ni destinations.

Compile et vérifie d'abord les anciennes sources propres aux mêmes adresses.
Seuls les corps propres plus courts sont remplacés ; tous les symboles et
hooks restent fixes. Le padding est placé après RTS, jamais dans la boucle.
--cycles OS1.13 --base recette-lfo.json --output recette-lfo-fast.json
"""
import argparse,copy,json,pathlib,shutil,subprocess,tempfile
from chord_keys_pr87 import load_stock
import build
SRC=pathlib.Path(__file__).parent/'machines/lfo_secondary'
def assemble(text,at,cross):
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);(p/'f.s').write_text(text);(p/'f.ld').write_text('SECTIONS { .text '+hex(at)+' : { *(.text*) } }')
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'f.o'),str(p/'f.s')],check=True)
  subprocess.run([cross+'ld','-T',str(p/'f.ld'),'-o',str(p/'f.elf'),str(p/'f.o')],check=True,stderr=subprocess.PIPE)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'f.elf'),str(p/'f.bin')],check=True)
  return (p/'f.bin').read_bytes()
def generate(stock,base):
 t=copy.deepcopy(base);s={k:int(v,16) for k,v in t['symbols'].items()};cross=next((x for x in ('m68k-elf-','m68k-linux-gnu-') if shutil.which(x+'as')),None)
 if not cross:raise RuntimeError('binutils ColdFire requis')
 mixer=(SRC/'mix.s').read_text()
 copier='    .text\n    .globl lf2_copy_frame\n'+(SRC/'dispatch.s').read_text().split('lf2_copy_frame:\n',1)[1]
 copier=copier.replace('    movel #118,%d0','lf2_copy_frame:\n    movel #118,%d0',1)
 changes=[]
 for name,oldsrc,pair,replacement in (
  ('lf2_mix',mixer,'    movew %a1@+,%d1\n    movew %d1,%a0@+','    movew %a1@+,%a0@+'),
  ('lf2_copy_frame',copier,'    movel %a0@+,%d1\n    movel %d1,%a1@+','    movel %a0@+,%a1@+')):
  assert oldsrc.count(pair)==1
  at=s[name];old=assemble(oldsrc,at,cross);new=assemble(oldsrc.replace(pair,replacement),at,cross)
  assert len(new)<len(old) and (len(old)-len(new))%2==0
  w=next(w for w in t['writes'] if build.BASE+w['off']<=at<build.BASE+w['off']+len(bytes.fromhex(w['new'])))
  own=bytearray.fromhex(w['new']);off=at-(build.BASE+w['off']);assert own[off:off+len(old)]==old,(name,'source/base divergent')
  own[off:off+len(old)]=new+b'\x4e\x71'*((len(old)-len(new))//2);w['new']=own.hex()
  changes.append(dict(symbol=name,at=hex(at),old_size=len(old),new_size=len(new)))
 assert t['symbols']==base['symbols'];build.apply_writes(stock,[t]);t['performance_copy']=dict(changes=changes,scope='Copies de frames seulement ; DSP et cadence inchangés.',hardware_tested=False)
 return t
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--base',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();t=generate(load_stock(a.cycles),json.loads(pathlib.Path(a.base).read_text()));out=pathlib.Path(a.output);text=json.dumps(t,ensure_ascii=False,indent=1)+'\n'
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : copies propres vérifiées, symboles fixes, empreinte inchangée')
if __name__=='__main__':main()
