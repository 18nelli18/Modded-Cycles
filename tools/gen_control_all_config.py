#!/usr/bin/env python3
"""Control All Config MIT de durchgemacht, relogé pour Supermodel (note77).

Sources épinglées429563bf13feb05edd0c7510efbc9f719b3741ff ; les cinq
trampolines rejouent les octets officiels. Sections séparées pour utiliser
les queues libres des masques sans déplacer les autres mods.
"""
import argparse,json,pathlib,re,shutil,struct,subprocess,tempfile
import build,sprites
from chord_keys_pr87 import load_stock
SRC=pathlib.Path(__file__).parent/'machines/control_all_config/control_all_config.s'
PIN='429563bf13feb05edd0c7510efbc9f719b3741ff'
HOOKS=((0x4001d6f8,'20522668007c','cac_loop1'),(0x4001d5a2,'20522f032f02','cac_loop2'),(0x4001ebd2,'205248780020','cac_loop3'),(0x4001ac7a,'2f022f034e92','cac_loop4'),(0x400a2798,'2f022f054e94','cac_loop5'))
VT=((0x40100ee8,0x40024078,'cac_keys'),(0x40100f98,0x40023d8c,'cac_leds'))
def source():
 text=SRC.read_text().replace('.section .cac_a,"ax"','.section .cac_state,"ax"').replace('.section .cac_b,"ax"','')
 for name in ('cac_skip',*('cac_loop'+str(i) for i in range(1,6)),'cac_keys','cac_leds'):
  text=text.replace('.globl  '+name,'.section .'+name+',"ax"\n        .globl  '+name,1)
 # Demande A.V. : aucun passe-droit pour la piste active. Garder les adresses.
 begin=text.index('cac_skip:\n');end=text.index('\n\n\n| Each loop entry',begin)
 text=text[:begin]+'''cac_skip:
        moveq   #0,%d1
        move.b  cac_mask,%d1
        btst    %d0,%d1
        beq.s   1f
        moveq   #1,%d0
        rts
1:      moveq   #0,%d0
        rts
        .space 52-(.-cac_skip),0
'''+text[end:]
 # Le LED reflète l'inclusion, également pour la piste active.
 old='''1:      moveq   #0,%d1
        move.b  cac_mask,%d1
        moveq   #2,%d0
        btst    %d2,%d1
        beq.s   2f
        moveq   #1,%d0
2:      pea     OS_LED_ON'''
 new='''1:      move.l  %d2,%d0
        jsr     cac_skip
        tst.l   %d0
        beq.s   2f
        moveq   #1,%d0
        bra.s   3f
2:      moveq   #2,%d0
3:      pea     OS_LED_ON'''
 assert text.count(old)==1;return text.replace(old,new)
def generate(stock,catalog):
 cross=next((x for x in ('m68k-elf-','m68k-linux-gnu-') if shutil.which(x+'as')),None)
 if not cross:raise RuntimeError('binutils ColdFire requis')
 used=[(build.BASE+w['off'],build.BASE+w['off']+len(bytes.fromhex(w['new']))) for t in catalog for w in t['writes']]
 gaps=[]
 for mask,row in sprites.MASKS.items():
  if len(row)!=4 or mask==0x4018dba8:continue # réserve optimisation OFF LFO
  cursor=mask
  for lo,hi in sorted((max(mask,lo),min(mask+row[0],hi)) for lo,hi in used if lo<mask+row[0] and mask<hi):
   if cursor<lo:gaps.append([cursor+(cursor&1),lo,mask])
   cursor=max(cursor,hi)
  if cursor<mask+row[0]:gaps.append([cursor+(cursor&1),mask+row[0],mask])
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);(p/'cac.s').write_text(source());subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'cac.o'),str(p/'cac.s')],check=True)
  sections=[]
  for line in subprocess.check_output([cross+'objdump','-h',str(p/'cac.o')],text=True).splitlines():
   x=line.split()
   if len(x)>3 and x[1].startswith('.cac_') and int(x[2],16):sections.append((x[1],int(x[2],16)))
  chosen=[]
  for name,size in sorted(sections,key=lambda x:-x[1]):
   options=[g for g in gaps if g[1]-g[0]>=size];assert options,('place insuffisante',name,size)
   g=min(options,key=lambda g:g[1]-g[0]);at=g[0];chosen.append((name,at,size,g[2]));g[0]=(at+size+1)&~1
  script='SECTIONS {\n'+''.join(f'{name} {at:#x} : {{ *({name}) }}\n' for name,at,_,_ in chosen)+' /DISCARD/ : { *(*) }\n}\n';(p/'cac.ld').write_text(script)
  subprocess.run([cross+'ld','-T',str(p/'cac.ld'),'-o',str(p/'cac.elf'),str(p/'cac.o')],check=True)
  syms={x[2]:int(x[0],16) for l in subprocess.check_output([cross+'nm',str(p/'cac.elf')],text=True).splitlines() if len(x:=l.split())==3}
  writes=[]
  for name,at,size,mask in chosen:
   f=p/(name+'.bin');subprocess.run([cross+'objcopy','-O','binary','-j',name,str(p/'cac.elf'),str(f)],check=True);code=f.read_bytes();assert len(code)==size
   writes.append(dict(off=at-build.BASE,old=stock[at-build.BASE:at-build.BASE+size].hex(),new=code.hex()))
   if name.startswith('.cac_loop'):
    hook=next(h for h in HOOKS if h[2]==name[1:]);assert code[12:18].hex()==hook[1]
    assert code[18:24]==b'\x4e\xf9'+struct.pack('>I',hook[0]+6)
  for mask in sorted({x[3] for x in chosen}):
   size,_,_,shared=sprites.MASKS[mask];assert stock[mask-build.BASE:mask-build.BASE+size]==stock[shared-build.BASE:shared-build.BASE+size];writes.append(sprites.redirect_write(mask))
 for at,old,name in HOOKS:
  assert stock[at-build.BASE:at-build.BASE+6].hex()==old
  writes.append(dict(off=at-build.BASE,old=old,new=(b'\x4e\xf9'+struct.pack('>I',syms[name])).hex()))
 for at,old,name in VT:
  assert stock[at-build.BASE:at-build.BASE+4]==struct.pack('>I',old)
  writes.append(dict(off=at-build.BASE,old=struct.pack('>I',old).hex(),new=struct.pack('>I',syms[name]).hex()))
 t=dict(id='control-all-config',order=46,name='Choix des pistes Control All',device='Model:Cycles',os='1.13',section=3,status='experimental',requires=[],conflicts=[],upstream_commit=PIN,active_track_excludable=True,symbols={k:hex(v) for k,v in sorted(syms.items()) if k.startswith('cac_')},writes=sorted(writes,key=lambda w:w['off']),placement=[dict(section=n,at=hex(a),size=z,mask=hex(m)) for n,a,z,m in chosen],description=['TRACK + TRIG1–6 choisit les pistes Control All ; piste active aussi excluable.','MIT durchgemacht et Claude ; choix RAM, reset au démarrage ; LED selon masque sans exception active.'])
 build.apply_writes(stock,catalog+[t]);return t
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--catalog',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();stock=load_stock(a.cycles);t=generate(stock,json.loads(pathlib.Path(a.catalog).read_text())['tweaks']);text=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : Control All Config '+str(sum(x['size'] for x in t['placement']))+' octets, sept accroches libres, catalogue compatible')
if __name__=='__main__':main()
