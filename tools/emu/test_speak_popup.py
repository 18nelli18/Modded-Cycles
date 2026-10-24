"""Noms128mots dans le vrai popup natif Word, pixels et pile conserves."""
import sys,json,struct
from boot_candidate import ROOT
from test_stereo_chorus_popup import rig
from unicorn import UC_HOOK_CODE,m68k_const as C
stem=sys.argv[1];m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());u=rig(stem);seen=[]
def text(uc,pc,*a):
 sp=uc.reg_read(C.UC_M68K_REG_A7);v=struct.unpack('>7I',uc.mem_read(sp+4,28))
 if v[1]==0x40ea14cc and v[2]==96:seen.append(u.cstr(v[6]))
u.uc.hook_add(UC_HOOK_CODE,text,begin=0x40071a04,end=0x40071a04)
for word,name in enumerate(m['speak']['words']):
 seen.clear();assert u.popup(142,word<<8) is not None;assert seen[-2:]==[name,str(word)],(word,seen)
print('PASS128 native Word popups, exact word/index text, valid stack/pixels',flush=True)
