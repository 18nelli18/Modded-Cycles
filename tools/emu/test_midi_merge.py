#!/usr/bin/env python3
"""Relais ColdFire : CC/notes/running status/SysEx, saturation et IRQ."""
import argparse,pathlib,subprocess,tempfile
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);args=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 r=Rig(main_os_from_syx(args.cycles),{'writes':[]},{'writes':[],'symbols':{}})
 with tempfile.TemporaryDirectory() as temp:
  p=pathlib.Path(temp)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'m.o'),str(root/'tools/machines/midi_thru/merge.s')],check=True)
  subprocess.run([cross+'ld','-Ttext=0x930e0000','-e','mm_feed','-o',str(p/'m.elf'),str(p/'m.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'m.elf'),str(p/'m.bin')],check=True)
  r.u.mem_write(0x930e0000,(p/'m.bin').read_bytes());r.s=symbols(cross,p/'m.elf')
 ctx=0x93060000;sent=[];realtime=[]
 def send(a):
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0
  sent.append(bytes(r.u.mem_read(a[1],a[0])));return 0
 r.stubs[0x40001100]=send;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40001100,end=0x40001100)
 def reset():
  r.u.mem_write(ctx,bytes(8256));r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);sent.clear();realtime.clear()
 def feed(data,ipl=4):
  for b in data:
   sr=0x2000|(ipl<<8);r.u.reg_write(mk.UC_M68K_REG_SR,sr)
   result=r.call('mm_feed',ctx,b)
   assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x2700==sr
   if result==2:realtime.append(b)
 def drain(n=8):
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);return r.call('mm_service',ctx,n)
 for status in range(0x80,0xf0):
  reset();length=1 if status>>4 in (0xc,0xd) else 2
  feed([status,*range(length),*range(10,10+length)])
  assert drain()==2
  assert sent==[bytes([status,*range(length)]),bytes([status,*range(10,10+length)])],(status,sent)
 print('ok : tous les canaux/types, statut explicite pour chaque message et running status')
 reset();feed([0xb6,74]);assert drain()==0
 # Une note-off locale passe entre les octets entrants, sans transmettre le fragment CC.
 sent.append(bytes([0x86,60,0]));feed([100,74,90]);assert drain()==2
 assert sent==[bytes([0x86,60,0]),bytes([0xb6,74,100]),bytes([0xb6,74,90])]
 print('ok : cutoff CC fragmenté + note-off locale + running status sans corruption')
 reset();feed([0xf1,1,0xf2,2,3,0xf3,4,0xf6,0xf7]);assert drain()==5
 assert sent==[bytes(x) for x in ([0xf1,1],[0xf2,2,3],[0xf3,4],[0xf6],[0xf7])]
 reset();feed([0x90,60,0xf8,100,0xfa,61,0xfe,90]);assert drain()==2
 assert realtime==[0xf8,0xfa,0xfe] and sent==[b'\x90\x3c\x64',b'\x90\x3d\x5a']
 print('ok : commun système et realtime ne modifient pas le running status canal')
 reset();sysex=bytes([0xf0]+[1]*1022+[0xf7]);feed(sysex);assert drain()==1 and sent==[sysex]
 reset();feed([0xf0]+[1]*1023+[0xf7]);assert drain()==0 and r.r32(ctx+20)==1
 feed([0xb6,74,100]);assert drain()==1 and sent==[b'\xb6\x4a\x64']
 reset();feed([0xf0,1,2,0x86,60,0]);assert drain()==1 and sent==[b'\x86\x3c\x00']
 print('ok : SysEx entier1024, débordement jeté entier/compté, resynchronisation')
 reset();feed([0xb6,74,1]+[x for i in range(1,10) for x in (74,i)])
 assert r.r32(ctx+16)==7 and r.r32(ctx+20)==3
 assert drain()==7 and len(sent)==7
 for i in range(40):
  feed([74,i]);assert drain()==1 and sent[-1]==bytes([0xb6,74,i])
 print('ok : saturation sans écrasement, retour running status et plusieurs tours de file')
 reset();feed([0xb6,74,99]);before=bytes(r.u.mem_read(ctx,8256))
 for ipl in range(1,8):
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8));assert r.call('mm_service',ctx,8)==0
  assert bytes(r.u.mem_read(ctx,8256))==before and not sent
 assert drain(0)==0 and drain()==1
 print('ok : writer DIN seulement IPL0, aucun retrait ni attente depuis IRQ')
 print('Limite : writer physique simulé ; intégration RX/tâche et capacité DMA à vérifier')
if __name__=='__main__':main()
