#!/usr/bin/env python3
"""Animation SUPERMODEL et signature by A.V., fonte originale5×7 (sans extraction).

Corps natif0x40053a6c..0x40053e74 seulement, même1,8s que l'origine.
--cycles firmware/model-cycles_OS1.13.syx --output work/supermodel-startup/boot-anim.json [--tested]
"""
import argparse,hashlib,json,pathlib,struct,tempfile,subprocess
import build
from gen_boot_anim import BODY,BODY_END,TASK_PEA
from gen_seq_gen import STOCK
from test_sdvintage import main_os_from_syx
ROOT=pathlib.Path(__file__).resolve().parents[1]
W,H,NF=128,64,80
TITLE='SUPERMODEL';CREDIT='by A.V.'
EDITION=''

FONT={
'T':['11111','00100','00100','00100','00100','00100','00100'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'N':['10001','11001','11001','10101','10011','10011','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'b':['10000','10000','11110','10001','10001','10001','11110'],
'y':['00000','10001','10001','01111','00001','10001','01110'],
' ':['000']*7,
'A':['01110','10001','10001','11111','10001','10001','10001'],
'.':['0','0','0','0','0','1','1'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
}
def columns(text,scale):
 cols=[];ends=[]
 for i,ch in enumerate(text):
  glyph=FONT[ch]
  for x in range(len(glyph[0])):
   value=sum(1<<(15-y*scale-yy) for y in range(7) for yy in range(scale) if glyph[y][x]=='1')
   cols.extend([value]*scale)
  ends.append(len(cols))
  if i<len(text)-1:cols.extend([0]*scale)
 return cols,ends
TC,TE=columns(TITLE,2);CC,CE=columns(CREDIT,1)
TITLE_X,TITLE_Y,TITLE_H=5,21,14
CREDIT_X,CREDIT_Y,CREDIT_H=TITLE_X+len(TC)-len(CC),44,7
TITLE_START,LINE_START,LINE_Y,CREDIT_START=8,30,38,46
assert TITLE_X+len(TC)<=W and CREDIT_X+len(CC)==TITLE_X+len(TC)
def frames():
 result=[]
 for f in range(NF):
  image=[[0]*W for _ in range(H)]
  for text,ends,start,step,x,y,height in ((TC,TE,TITLE_START,2,TITLE_X,TITLE_Y,TITLE_H),(CC,CE,CREDIT_START,2,CREDIT_X,CREDIT_Y,CREDIT_H)):
   if f>=start:
    count=ends[min((f-start)//step+1,len(ends))-1]
    for xx in range(count):
     for yy in range(height):image[y+yy][x+xx]=text[xx]>>(15-yy)&1
  if f>=LINE_START:
   for x in range(TITLE_X,TITLE_X+min((f-LINE_START)*6+1,len(TC))):image[LINE_Y][x]=1
  if EDITION and f>=56:
   ec,ee=columns(EDITION,1);x=(W-len(ec))//2;count=ee[min((f-56)//2+1,len(ee))-1]
   for xx in range(count):
    for yy in range(7):image[54+yy][x+xx]=ec[xx]>>(15-yy)&1
  result.append(image)
 return result

def compile_anim():
 consts=dict(NF=NF,TITLE_X=TITLE_X,TITLE_Y=TITLE_Y,TITLE_H=TITLE_H,TITLE_START=TITLE_START,TITLE_COUNT=len(TITLE),TITLE_WIDTH=len(TC),LINE_START=LINE_START,LINE_Y=LINE_Y,CREDIT_X=CREDIT_X,CREDIT_Y=CREDIT_Y,CREDIT_H=CREDIT_H,CREDIT_START=CREDIT_START,CREDIT_COUNT=len(CREDIT))
 cross=str(ROOT.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);(p/'supermodel.inc').write_text(''.join(f'.equ {k},{v}\n' for k,v in consts.items()))
  data=''
  if EDITION:
   ec,ee=columns(EDITION,1);consts.update(EDITION_ENABLED=1,EDITION_X=(W-len(ec))//2,EDITION_Y=54,EDITION_H=7,EDITION_START=56,EDITION_COUNT=len(EDITION))
   (p/'supermodel.inc').write_text(''.join(f'.equ {k},{v}\n' for k,v in consts.items()))
  for name,cols,ends in (('title',TC,TE),('credit',CC,CE)):
   data+=name+'_ends: .byte '+','.join(map(str,ends))+'\n.balign 2\n'+name+'_cols: .word '+','.join(map(str,cols))+'\n'
  if EDITION:data+='edition_ends: .byte '+','.join(map(str,ee))+'\n.balign 2\nedition_cols: .word '+','.join(map(str,ec))+'\n'
  (p/'supermodel_data.inc').write_text(data)
  subprocess.run([cross+'as','-march=cfv4e','-I',str(p),str(ROOT/'tools/machines/boot_supermodel/boot_supermodel.S'),'-o',str(p/'a.o')],check=True)
  subprocess.run([cross+'ld','-T',str(ROOT/'tools/machines/boot_anim/boot_anim.ld'),'--no-warn-rwx-segments','-o',str(p/'a.elf'),str(p/'a.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary','-j','.anim',str(p/'a.elf'),str(p/'a.bin')],check=True);code=(p/'a.bin').read_bytes()
 assert len(code)<=BODY_END-BODY,(len(code),BODY_END-BODY)
 return code

def generate(stock,tested=False):
 assert hashlib.sha256(stock).hexdigest()==STOCK
 at,old=TASK_PEA;assert stock[at-build.BASE:at-build.BASE+4].hex()==old
 assert stock[BODY-build.BASE:BODY-build.BASE+4].hex()=='4fefff80'
 code=compile_anim();t=dict(id='supermodel-startup',order=43,conflicts=['boot-anim'],name='Animation SUPERMODEL by A.V.',description=['SUPERMODEL apparaît lettre par lettre au démarrage, suivi d’un trait et de la signature by A.V. alignée à droite.'],device='Model:Cycles',os='1.13',section=3,status='tested' if tested else 'experimental',writes=[dict(off=BODY-build.BASE,old=stock[BODY-build.BASE:BODY-build.BASE+len(code)].hex(),new=code.hex())])
 build.apply_writes(stock,[t]);return t

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--output',default='work/supermodel-startup/boot-anim.json');ap.add_argument('--check',action='store_true');ap.add_argument('--tested',action='store_true',help='Marquer testé après validation matérielle rapportée.');a=ap.parse_args();t=generate(main_os_from_syx(a.cycles),tested=a.tested);p=pathlib.Path(a.output);s=json.dumps(t,ensure_ascii=False,indent=1)+'\n'
 if a.check:assert p.read_text()==s
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 print('ok : SUPERMODEL',len(bytes.fromhex(t['writes'][0]['new'])),'octets sur',BODY_END-BODY)
if __name__=='__main__':main()
