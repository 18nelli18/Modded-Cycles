"""Codec sampler : mêmes octets stock, état Sampler conservé sans fonctions TG globales."""
import pathlib,subprocess,random,struct
import test_lfo_plus as C
from chord_keys_pr87 import load_stock
stock=load_stock('firmware/model-cycles_OS1.13.syx');raw=pathlib.Path('work/supermodel-sampler-prototype/guard.bin').read_bytes();syms={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output(['m68k-elf-nm','work/supermodel-sampler-prototype/guard.elf'],text=True).splitlines() if len(r.split())==3 and r.split()[1]!='U'}
rng=random.Random(26);s=C.Rig(stock);p=C.Rig(stock);p.uc.mem_write(0x401ab750,raw)
for machine in range(6):
 for trial in range(5):
  snd=bytearray(C.sound_bytes(rng,C.DEFAULTS));snd[38]=machine
  for fn,label in [(C.SND_SAVE2,'snd_save2_hook'),(C.SND_SAVE1,'snd_save1_hook')]:
   records=[]
   for rig,entry in [(s,fn),(p,syms[label])]:
    rig.uc.mem_write(C.SOUND,bytes(snd));rig.uc.mem_write(C.REC,b'\xa5'*100);ret=rig.call(entry,C.REC,C.SOUND,check='save ABI');records.append((ret,rig.rd(C.REC,100)))
   assert records[0]==records[1],(machine,trial,label)
   if fn==C.SND_SAVE2:
    loaded=[]
    for rig,entry in [(s,C.SND_LOAD),(p,syms['snd_load_hook'])]:
     rig.uc.mem_write(C.SOUND2,b'\x55'*100);rig.uc.mem_write(C.REC,records[0][1]);ret=rig.call(entry,C.SOUND2,C.REC,check='load ABI');loaded.append((ret,rig.rd(C.SOUND2,100)))
    assert loaded[0]==loaded[1],(machine,trial,'load')
print('PASS 60 sauvegardes et 30 chargements stock : records/runtime/D0 identiques, ABI conservée')
snd=bytearray(C.sound_bytes(rng,C.DEFAULTS));snd[38]=6;snd[72:76]=b'\x12\x34\x56\x78'
p.uc.mem_write(C.SOUND,bytes(snd));p.uc.mem_write(C.REC,b'\xa5'*100);assert p.call(syms['snd_save2_hook'],C.REC,C.SOUND,check='Sampler save')&255==1;record=p.rd(C.REC,100);assert record[84:88]==b'\x12\x34\x56\x78'
p.uc.mem_write(C.SOUND2,b'\x55'*100);p.call(syms['snd_load_hook'],C.SOUND2,C.REC,check='Sampler load');assert p.rd(C.SOUND2+72,4)==b'\x12\x34\x56\x78';assert not C.FAIL,C.FAIL
print('PASS état mode/Slice Sampler sauvé/rechargé par le vrai codec OS ; stock ignoré par extension')
