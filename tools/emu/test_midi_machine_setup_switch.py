"""Fenetre Track Setup native conservee, schemas MIDI/audio et edition selon piste."""
import json,sys,pathlib,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_menu_render import Drawing
from test_midi_machine_ui import ROOT,SOUND,EVENT
from test_midi_machine_notes import PROJECT
import gen_sdvintage_7th as g7
from test_midi_entry import boot_case
from render_midi_bank import png
case=sys.argv[1] if len(sys.argv)>1 else 'build/macro-fine/usb-after'
img,mem,ts=boot_case(case);engine=next(t for t in ts if t.get('machine_selection')==1023);pay=int(engine['append']['dest'],16);blob=next(raw for at,raw in mem if at==pay)
r=Drawing(img,dict(hex=blob.hex(),symbols=engine['symbols'],machine=17),pay)
for at,raw in mem:r.u.mem_write(at,raw)
assert r.word(0x40108138)==r.s['mm_track_draw']
r.call(0x4005a274)
heap=[0x92400000]
def new(a):
 at=heap[0];heap[0]+=(a[0]+15)&~15;r.u.mem_write(at,bytes(a[0]));return at
for at,fn in ((0x400802e0,new),(0x400802ec,lambda a:0),(0x400cf044,lambda a:0),(0x400f4dc6,lambda a:1),(0x400f4e22,lambda a:0),(0x40069df6,lambda a:0)):
 r.stub(at,fn)
r.word(PROJECT,0x92070010);r.word(0x92070004,0)
r.call(0x400e7dbc)
icons=0x92500000;r.call(0x40070172,icons,9,9,0x40152c14,r.word(0x400b97f2));r.call(0x40070172,icons+28,9,9,0x40152c38,r.word(0x400b9816));r.word(0x40fe1fb0,icons)
root=0x92200000
r.call(0x40070172,0x40fe3310,48,22,0x4016bd98,r.word(0x400b12fe)) # vrai titre bitmap stock
r.call(0x4003e020,root)
assert r.word(root)==0x40108094 and r.word(root+56)==0x40108128
app=0x920d0000;node=app+512;view=root+56
r.word(0x40fe4178,app);r.word(app+88,node);r.word(node+4,app+84);r.word(node+8,view)
canvas,fb=0x920c0000,0x920c1000;r.call(0x40070172,canvas,128,64,fb,0)

def draw(lane,machine):
 r.track=lane;r.u.mem_write(SOUND+lane*0x1000+38,bytes((machine,0)))
 r.u.mem_write(fb,bytes(1024));r.call(r.word(0x40108138),view,canvas)
 raw=bytes(r.u.mem_read(fb,1024));assert any(raw)
 return raw

def key(code,flags):
 r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,code,flags,0));return r.call(r.s['mm_ui_key'],EVENT)

def capture(name,raw):
 pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
 png(ROOT/f'build/midi-machine/setup-{name}.png',pixels)

# Commencer sur une piste audio, puis selectionner MIDI sans rouvrir.
stock=draw(1,0);capture('audio',stock)
midi=draw(0,17);capture('midi',midi);assert stock!=midi
assert r.call(r.s['mm_menu_row'])==0 and r.call(r.s['mm_menu_edit'])==0
assert key(32,16)==1;r.call(r.s['mm_encoder'],r.event(-1,-1))
assert r.call(r.s['mm_route_read'],SOUND+20,0)==15
# TRACK seul permet la selection sans fermer le setup.
assert key(2,1)==0 and r.call(r.s['mm_menu_edit'])==1
assert key(2,0)==0
for machine in range(17):
 actual=draw(1,machine)
 r.u.mem_write(fb,bytes(1024));r.call(0x400426fa,view,canvas)
 assert bytes(r.u.mem_read(fb,1024))==actual,('stock different',machine)
 before=bytes(r.u.mem_read(SOUND+0x1000+20,66))
 assert r.call(r.s['mm_encoder'],r.event(-1,1))==0
 assert bytes(r.u.mem_read(SOUND+0x1000+20,66))==before
 assert r.call(r.s['mm_menu_edit'])==0
 draw(0,17);assert r.call(r.s['mm_menu_row'])==0 and r.call(r.s['mm_menu_edit'])==0
 assert r.call(r.s['mm_route_read'],SOUND+20,0)==15
# Une autre piste MIDI utilise son propre routage et commence en navigation.
draw(2,17);assert r.call(r.s['mm_menu_edit'])==0
assert key(32,16)==1;r.call(r.s['mm_encoder'],r.event(-1,-2))
assert r.call(r.s['mm_route_read'],SOUND+0x2000+20,0)==14
assert r.call(r.s['mm_route_read'],SOUND+20,0)==15
# BACK est delegue pour fermer la vraie fenetre ; aucun overlay residuel.
assert key(12,1)==0;r.u.mem_write(view+48,b'\1')
assert r.call(r.s['mm_draw'],0,canvas)==0
print('PASS vraie TrackMenuView construite une fois : audio -> MIDI ->17machines audio -> MIDI ; rendu audio identique stock, DATA delegue, routages par piste, BACK natif')
