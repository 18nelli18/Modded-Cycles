"""Reproduction reelle : poll/initialisation MIDI entre les rotations."""
from pathlib import Path
W=Path(__file__).resolve().parents[2]
s=(W/'tools/emu/validate_scroll_roundtrip140.py').read_text()
s=s.replace("else 'v140'", "else 'v141'").replace('(64,90,79,110,88,25)','(64,90,79,110,24,25)')
s=s.replace("u.hooks[0x400802e0]=('alloc',0x93220000);tick=0", """u.hooks[0x400802e0]=('alloc',0x93220000);tick=0
 u.uc.mem_write(0x40fe4178,bytes(4))
 # Le vrai poll initialise les mots CC/LFO et leur tag, puis les nettoie
 # apres sortie de MIDI. C'etait absent des precedentes fixtures de scroll.
 def find(tree,key):
  if isinstance(tree,dict):
   if key in tree:return tree[key]
   for value in tree.values():
    found=find(value,key)
    if found is not None:return found
  return None
 poll=find(m,'mx_poll');assert poll
 u.hooks[0x467900e6]=('MIDI-notes-cleanup',0)
""")
s=s.replace('u.call(0x400a2712,this,delta,0,0)', "u.call(0x400a2712,this,delta,0,0);u.hooks[0x4001e318]=('machine',u.uc.mem_read(snd+38,1)[0]);u.call(poll)")
s=s.replace(' for machine in order[1:]:turn(1);assert u.uc.mem_read(snd+38,1)[0]==machine;forward[machine]=values()', ''' for machine in order[1:]:
  turn(1);assert u.uc.mem_read(snd+38,1)[0]==machine;forward[machine]=values()
  if machine==17:
   cc_read=find(m,'mm_cc_read');assert cc_read
   for knob in (0,1,2,3,4,5,6,7,9):assert u.call(cc_read,snd+20,knob)<128,('unassigned CC became assigned',lane,knob)
''')
exec(compile(s,str(W/'tools/emu/validate_scroll_roundtrip140.py'),'exec'))
