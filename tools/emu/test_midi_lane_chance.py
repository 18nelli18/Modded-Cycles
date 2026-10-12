#!/usr/bin/env python3
"""Prototype chance B compilé : héritage/0/100, aucune donnée audio modifiée."""
import argparse,pathlib,subprocess,tempfile
from test_midi_lane_page import make,PAT
from test_sdvintage import main_os_from_syx
from test_seq_gen_menu import RAW
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);a=ap.parse_args()
 r=make(main_os_from_syx(a.cycles),repeat=True);r.call('ml_repeat_prepare_ui')
 settings=r.r32(r.s['ml_repeat_edit_settings']);assert settings
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);elf=p/'chance.elf'
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'chance.o'),str(root/'tools/machines/midi_lanes/chance.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'conditions.o'),str(root/'tools/machines/midi_lanes/conditions.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'history.o'),str(root/'tools/machines/midi_lanes/condition_history.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'decode.o'),str(root/'tools/machines/midi_lanes/condition_decode.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'run.o'),str(root/'tools/machines/midi_lanes/condition_run.s')],check=True)
  subprocess.run([cross+'ld','-Ttext=0x930c0000','-e','ml_chance_accept','-o',str(elf),str(p/'chance.o'),str(p/'conditions.o'),str(p/'history.o'),str(p/'decode.o'),str(p/'run.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(elf),str(p/'chance.bin')],check=True)
  r.u.mem_write(0x930c0000,(p/'chance.bin').read_bytes());r.s.update(symbols(cross,elf))
 # Décodage des64 choix depuis les noms du vrai OS, sans recopier sa table.
 import struct
 out=0x930d0200
 for code in range(64):
  r.u.mem_write(out,b'X'*12)
  assert r.call('ml_condition_decode',code,out)==1
  kind,aa,b=struct.unpack('>3I',r.u.mem_read(out,12))
  ptr=r.r32(0x40108f54+code*4);label=bytes(r.u.mem_read(ptr,12)).split(b'\0')[0].decode('ascii')
  if code<8:assert (kind,aa,b)==(code+1,0,0)
  elif ':' in label:assert (kind,aa,b)==(9,*map(int,label.split(':')))
  else:assert (kind,aa,b)==(0,int(label.replace('%','')),0)
 for code in (64,0xffffffff):
  r.u.mem_write(out,b'X'*12)
  assert r.call('ml_condition_decode',code,out)==0
  assert bytes(r.u.mem_read(out,12))==b'X'*12
 # Rendu natif : traverser le vrai formatter de condition sur les64 choix.
 r.call(0x400e7dbc)
 r.call(0x40070172,0x93006000,128,64,0x93090000,0)
 markers=[];current=[0]
 def marker(uc,address,size,user):
  sp=uc.reg_read(mk.UC_M68K_REG_A7)
  if r.r32(sp)==0x40050138:markers.append(current[0])
 r.u.hook_add(UC_HOOK_CODE,marker,begin=0x4007031c,end=0x4007031c)
 for code in range(64):
  current[0]=code
  r.call(0x40050046,0,code<<8,0x93006000,64,20)
 assert markers==[1,3,5,7],markers
 print('ok : vrai formatter/dessin condition OS exécuté pour les64 choix')
 print('ok : décode les64 conditions natives, valeurs/ordre OS et refus hors domaine sans écriture')
 # Familles conditionnelles : toutes combinaisons d'historique/fill/premier.
 for fill in (0,1):
  for prev in (0,1):
   for nei in (0,1):
    for phase in (0,1,7):
     expected=(fill,1-fill,prev,1-prev,nei,1-nei,int(phase==0),int(phase!=0))
     for kind,value in enumerate(expected,1):
      assert r.call('ml_condition_eval',kind,0,0,phase,fill,prev,nei,0)==value
 for b in range(1,9):
  for aa in range(1,b+1):
   results=[r.call('ml_condition_eval',9,aa,b,phase,0,0,0,0) for phase in range(b)]
   assert results==[int(phase==aa-1) for phase in range(b)]
 for pct in range(101):
  assert sum(r.call('ml_condition_eval',0,pct,0,0,0,0,0,n) for n in range(100))==pct
 for aa,b,phase in ((0,2,0),(3,2,0),(1,9,0),(1,2,2)):
  assert r.call('ml_condition_eval',9,aa,b,phase,0,0,0,0)==0
 assert r.call('ml_condition_eval',10,0,0,0,0,0,0,0)==0
 print('ok : conditions FILL/PRE/NEI/1ST et inverses, 36 ratios A:B, probabilité et bornes')
 # Historique six voies : PRE ne remplace pas, voisin B, cycles indépendants.
 hist=0x930d0100;r.u.mem_write(hist-4,b'HEAD'+bytes(96)+b'TAIL')
 assert r.call('ml_cond_init',hist)==1
 for lane in range(6):
  assert r.call('ml_cond_first',hist,lane)==1
  assert r.call('ml_cond_neighbor',hist,lane)==0
 assert r.call('ml_cond_remember',hist,0,0,1)==1
 assert r.call('ml_cond_neighbor',hist,1)==1
 for kind in (3,4):
  r.call('ml_cond_remember',hist,0,kind,0)
  assert r.call('ml_cond_previous',hist,0)==1
 for turn in range(1,65):
  assert r.call('ml_cond_advance',hist,2)==1
  assert r.call('ml_cond_first',hist,2)==0
  for b in range(1,9):assert r.call('ml_cond_phase',hist,2,b)==turn%b
  assert r.call('ml_cond_first',hist,1)==1
 assert bytes(r.u.mem_read(hist-4,4))==b'HEAD' and bytes(r.u.mem_read(hist+96,4))==b'TAIL'
 before=bytes(r.u.mem_read(hist,96))
 for lane in (6,0xffffffff):
  assert r.call('ml_cond_advance',hist,lane)==0
  assert r.call('ml_cond_remember',hist,lane,3,1)==0
 assert r.call('ml_cond_init',hist+1)==0
 assert r.call('ml_cond_advance',0,0)==0
 assert bytes(r.u.mem_read(hist,96))==before
 print('ok : historique B six voies, PRE stable, NEI voisin B, premier passage et cycles modulo1..8')
 # Parcours code natif -> decode -> état B -> décision -> mémoire.
 r.call('ml_cond_init',hist)
 assert r.call('ml_condition_run',hist,0,0,1,50)==1
 assert r.call('ml_condition_run',hist,0,2,0,50)==1
 assert r.call('ml_condition_run',hist,0,3,0,50)==0
 assert r.call('ml_cond_previous',hist,0)==1
 assert r.call('ml_condition_run',hist,1,4,0,50)==1
 assert r.call('ml_condition_run',hist,2,6,0,50)==1
 r.call('ml_cond_advance',hist,2)
 assert r.call('ml_condition_run',hist,2,6,0,50)==0
 assert r.call('ml_condition_run',hist,2,7,0,50)==1
 r.call('ml_cond_init',hist)
 # Les ratios de chaque code natif suivent la phase privée correspondante.
 for code in range(29,64):
  r.call('ml_cond_init',hist);r.call('ml_condition_decode',code,out)
  _,aa,b=struct.unpack('>3I',r.u.mem_read(out,12))
  for turn in range(b*3):
   assert r.call('ml_condition_run',hist,3,code,0,0)==int(turn%b==aa-1)
   r.call('ml_cond_advance',hist,3)
 before=bytes(r.u.mem_read(hist,96))
 for lane,code,sample in ((6,0,0),(0,64,0),(0,0,100)):
  assert r.call('ml_condition_run',hist,lane,code,1,sample)==0
  assert bytes(r.u.mem_read(hist,96))==before
 print('ok : parcours complet des conditions natives avec mémoire PRE/NEI/1ST et trois cycles de chaque ratio')
 # RNG par voie : référence xorshift, tirages bornés, autres seeds intacts.
 seedptr=0x930d0000;r.u.mem_write(seedptr,bytes(24));ref=0
 for n in range(4096):
  ref=ref or 0x6d2b79f5
  ref^=(ref<<13)&0xffffffff;ref^=ref>>17;ref^=(ref<<5)&0xffffffff
  expected=((ref>>16)*100)>>16
  assert r.call('ml_chance_sample',seedptr)==expected
  assert r.r32(seedptr)==ref
  assert bytes(r.u.mem_read(seedptr+4,20))==bytes(20)
 assert r.call('ml_chance_sample',0)==0xffffffff
 assert r.call('ml_chance_sample',seedptr+1)==0xffffffff
 notes=bytes(r.u.mem_read(PAT,1584));sound=bytes(r.u.mem_read(RAW,722));locks=settings+8
 assert r.call('ml_chance_percent',settings,locks,0)==100
 assert r.call('ml_chance_set',settings,0,37)==1
 for step in (0,31,63):
  assert r.call('ml_chance_percent',settings,locks,step)==37
  for pct in range(101):
   before=bytes(r.u.mem_read(settings,3120));assert r.call('ml_chance_set',locks,step,pct)==1
   after=bytes(r.u.mem_read(settings,3120));at=8+step*8+7
   assert after[:at]==before[:at] and after[at+1:]==before[at+1:]
   assert r.call('ml_chance_percent',settings,locks,step)==pct
   assert sum(r.call('ml_chance_accept',settings,locks,step,n) for n in range(100))==pct
  assert r.call('ml_chance_clear',locks,step)==1
  assert r.call('ml_chance_percent',settings,locks,step)==37
 before=bytes(r.u.mem_read(settings,3120))
 for step,pct in ((64,50),(0xffffffff,50),(0,101),(0,0xffffffff)):
  assert r.call('ml_chance_set',locks,step,pct)==0
  assert bytes(r.u.mem_read(settings,3120))==before
 assert r.call('ml_chance_set',0,0,50)==0
 assert r.call('ml_chance_accept',settings,locks,0,100)==0
 assert bytes(r.u.mem_read(PAT,1584))==notes and bytes(r.u.mem_read(RAW,722))==sound
 print('ok : 0..100 % ×100 échantillons ×3 pas, héritage distinct de0, bornes et isolation des locks/audio')
 print('Limite : moteur de décision seul ; menu/knob et déclenchement non raccordés, non publié')
if __name__=='__main__':main()
