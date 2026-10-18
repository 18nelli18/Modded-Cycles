"""Note119 : vrais boots, gestes OS, editions FUNC et fenetres MACRO, avant/apres."""
import argparse,json,os,pathlib,sys,time
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig
from lofi_ui import UI,FTUN,PITCH,UI_REC,want_step,want_text
ROOT=HERE.parent.parent
CASES=os.environ.get('MACRO_LOFI_OUT','build/macro-lofi')

def load(prefix):
 img,mem,ts=boot_case(prefix)
 # Les petites charges copiees dans l'image sont deja dans img ; reunir la SDRAM.
 external=[(at,raw) for at,raw in mem if at>=0x43000000]
 lo=min(at for at,raw in external);hi=max(at+len(raw) for at,raw in external);raw=bytearray(hi-lo)
 for at,data in external:raw[at-lo:at-lo+len(data)]=data
 return UI(img,(lo,bytes(raw)),end=0x40000400+len(img)),img,mem,ts

def run(i):
 prefix=ROOT/f'{CASES}/{i}';a,_,_,_=load(str(prefix)+'-before');b,img,mem,ts=load(str(prefix)+'-after');meta=json.loads(pathlib.Path(str(prefix)+'-after.json').read_text());c=meta['case'];index=6+c['wizard']+(c['mask']&31).bit_count();nm=6+c['wizard']+c['mask'].bit_count();assert a.init_ok and b.init_ok
 assert a.lookup(index,2,True) in (PITCH,FTUN),(i,index,a.lookup(index,2,True),a.bad,a.sp_ok)
 for machine in range(nm):
  for knob in range(2,16):
   for func in (False,True):
    got=b.lookup(machine,knob,func);expected=FTUN if machine==index and knob==2 and func else a.lookup(machine,knob,func)
    assert got==expected,(i,machine,knob,func,got,expected)
 print('PASS knob lookup, all machines and FUNC states',i,flush=True)
 assert b.lookup(index,2,True)==FTUN
 for cur in (0,0x100,0x3f00,0x4000,0x4080,0x4100,0x7e00,0x7f00,0x1234):
  for delta in (1,0x100,0x180,0x300,-1,-0x100,-0x300,0x7f00,-0x7f00):assert b.edit_func(FTUN,cur,delta)==want_step(cur,delta),(i,cur,delta)
 assert [b.text(FTUN,n<<8) for n in range(128)]==[want_text(n) for n in range(128)]
 for n in (0,1,31,63,64,65,100,127):
  actual=b.popup(FTUN,n<<8);expected=b.popup(FTUN,n<<8,text_path=True);assert actual is not None and actual==expected and not actual[1],(i,n)
 for d in range(77):
  if d!=FTUN:assert bytes(a.uc.mem_read(UI_REC+100*d,100))==bytes(b.uc.mem_read(UI_REC+100*d,100)),(i,d)
 # Le cache disque ne doit pas ecraser le helper place a la fin du dernier payload.
 q=next(t for t in ts if t['id'] in ('macro-lofi-test','macro-lofi'));at=int(q['symbols']['ml_knob'],16);r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
 for start,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(start,size)
 for start,data in mem:u.mem_write(start,data)
 before=bytes(u.mem_read(at,436));r.call(0x4007929c);assert bytes(u.mem_read(at,436))==before,(i,'cache overwrites helper')
 print('PASS FUNC edits 81 cases, all 128 labels, eight real popup renders, other UI records and cache preserved',i,flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',type=int);p.add_argument('--watch',action='store_true');a=p.parse_args()
 for i in ([a.case] if a.case is not None else range(8)):
  start=time.monotonic()
  while not (ROOT/f'{CASES}/{i}-after.syx').exists():
   if not a.watch or time.monotonic()-start>1200:raise AssertionError(('missing case',i))
   time.sleep(2)
  run(i)
 print('PASS MACRO upstream lo-fi port',flush=True)
if __name__=='__main__':main()
