"""Vrai setMachine : retention bornee, transitions MIDI/Wizard et resets explicites."""
import sys,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from boot_candidate import ROOT,boot
import test_sdvintage_7th as T
import test_model_tg_syntakt as M
from unicorn import m68k_const as C
SLOTS=[10,18,11,12,13,14]
def fixture(stem):
 im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));u=T.UI(im);u.uc.mem_write(T.BASE,im);u.uc.mem_map(0x46700000,len(mem[0][1]));u.uc.mem_map(0x80000000,0x20000);u.uc.mem_write(*mem[0]);u.call(0x4005a274);M.fill_records(u);obj,snd=T.fake_track(u,0);del u.hooks[0x40014072]
 for a,v in {0x400cf866:0x93a00000,0x4000eb90:0x93a00000,0x40012412:0,0x400cf9a8:0x93a00000,0x4006bdfe:0,0x4000eb9c:0x93a00000,0x40009c1a:obj,0x400f44c6:0,0x4001416c:0}.items():u.hooks[a]=(hex(a),v)
 return u,obj,snd

def wizard_roundtrips(stem):
 # Vrai chemin molette -> setMachine -> copie vectorielle -> snapshot natif.
 # Le snapshot a la duree de vie du menu MACHINES, exactement comme le stock.
 profile=json.loads((ROOT/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text())
 sy={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()}
 cases=0
 for lane in range(6):
  for mode in range(7):
   u,obj,snd=fixture(stem)
   for fn in (0x400f44c6,0x4001416c):del u.hooks[fn]
   u.hooks[0x40012412]=('lane',lane)
   u.hooks[0x400802e0]=('alloc',0x93210000)
   u.hooks[0x400802ec]=('free',0)
   this=0x93900000;data=0x93200000
   for k in range(6):u.uc.mem_write(this+0x70+4*k,struct.pack('>i',6))
   vals=[65*256,102*256,19*256,111*256,83*256,44*256]
   u.uc.mem_write(snd,bytes(100));u.uc.mem_write(snd+38,b'\x06\x00')
   for sl,value in zip(SLOTS,vals):u.uc.mem_write(snd+20+2*sl,struct.pack('>H',value))
   u.uc.mem_write(snd+60,struct.pack('>H',vals[1]))
   meta=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())
   u.uc.reg_write(C.UC_M68K_REG_D2,lane)
   u.call(meta['keep_params']['symbols']['kr_snapshot'],obj)
   vector=bytes(u.uc.mem_read(T.SCRATCH,12));u.uc.mem_write(this+136+12*lane,vector)
   u.hooks[0x400802e0]=('alloc',0x93220000)
   # Tous les champs d'options, dont Slice, stereo et sens, avec un etat valide.
   fields=[mode,2,1,3,1,4,2,5,4,1,2,3,2,1];ranges=[7,5,2,7,3,6,4,7,7,2,3,4,3,2]
   packed=0
   for value,radix in reversed(list(zip(fields,ranges))):packed=packed*radix+value
   packed|=0x70000000;u.uc.mem_write(snd+72,struct.pack('>I',packed))
   protected=[]
   for name in ['track_hash','track_slot','sl_cfg','sl_N','sl_S','sl_md','sl_ct','loop_mode','gr_dir','lp_type']:
    if name in sy:
     at=sy[name]+4*lane;value=(0x13572468 if name=='track_hash' else 3 if name=='track_slot' else 5 if name=='sl_cfg' else 16 if name=='sl_N' else 7 if name=='sl_S' else mode if name=='loop_mode' else 1)
     u.uc.mem_write(at,struct.pack('>I',value));protected.append((at,bytes(u.uc.mem_read(at,4))))
   before=bytes(u.uc.mem_read(snd,100))
   u.call(0x400a2712,this,1,0,0);assert u.uc.mem_read(snd+38,1)[0]==7
   u.call(0x400a2712,this,0xffffffff,0,0)
   assert u.uc.mem_read(snd+38,1)[0]==6
   assert bytes(u.uc.mem_read(snd,100))==before,('Wizard roundtrip',lane,mode,[(i,a,b) for i,(a,b) in enumerate(zip(before,u.uc.mem_read(snd,100))) if a!=b])
   assert all(bytes(u.uc.mem_read(at,4))==value for at,value in protected),('Wizard tables',lane,mode)
   assert not u.bad
   assert any(name=='alloc' for name,args in u.calls), 'Copie native non executee'
   cases+=1
 return cases

def wizard_control_all(stem):
 u,obj,snd=fixture(stem);meta=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())
 for fn in (0x400f44c6,0x4001416c,0x40009c1a):del u.hooks[fn]
 u.hooks[0x400802ec]=('free',0)
 # Getter externe de pistes : six objets distincts, le reste du parcours est natif.
 u.uc.mem_write(0x40009c1a,bytes.fromhex('4ef993500000'))
 u.uc.mem_write(0x93500000,bytes.fromhex('202f000848400680938000004e75'))
 this=0x93900000;records=[]
 for lane in range(6):
  ob=obj+0x10000*lane;vt=ob+0x1000;sd=ob+0x2000
  u.uc.mem_write(ob,struct.pack('>I',vt))
  for k in range(16):
   method=ob+0x3000+16*k;u.uc.mem_write(vt+4*k,struct.pack('>I',method));u.hooks[method]=('vt'+str(k),sd if k==10 else 0)
  u.uc.mem_write(sd,bytes(100));u.uc.mem_write(sd+38,b'\x06\x00')
  vals=[(64+lane)*256,(90+lane)*256,(12+lane)*256,(112+lane)*256,(80+lane)*256,(23+lane)*256]
  for sl,value in zip(SLOTS,vals):u.uc.mem_write(sd+20+2*sl,struct.pack('>H',value))
  u.uc.mem_write(sd+60,struct.pack('>H',vals[1]));u.uc.mem_write(sd+72,struct.pack('>I',0x700089d2))
  u.uc.mem_write(this+0x70+4*lane,struct.pack('>I',6));u.hooks[0x400802e0]=('alloc',0x93200000+0x1000*lane)
  u.uc.reg_write(C.UC_M68K_REG_D2,lane)
  u.call(meta['keep_params']['symbols']['kr_snapshot'],ob);u.uc.mem_write(this+136+12*lane,bytes(u.uc.mem_read(T.SCRATCH,12)))
  records.append((sd,bytes(u.uc.mem_read(sd,100))))
 u.hooks[0x400802e0]=('alloc',0x93220000)
 u.call(0x400a2712,this,1,1,0);assert [u.uc.mem_read(sd+38,1)[0] for sd,b in records]==[7]*6
 u.call(0x400a2712,this,0xffffffff,1,0)
 for lane,(sd,before) in enumerate(records):assert bytes(u.uc.mem_read(sd,100))==before,('control all Wizard',lane,[(i,a,b) for i,(a,b) in enumerate(zip(before,u.uc.mem_read(sd,100))) if a!=b])
 assert not u.bad
 return 6

def main():
 reports=[]
 for stem in (sys.argv[1:] or ['all-features-polivoks-cpu-trim-test-v47','no-filter-wizard-polivoks-cpu-trim-test-v47nf']):
  u,obj,snd=fixture(stem);r,ro,rs=fixture(stem.rsplit('-',1)[0]+'-v46'+('nf' if stem.endswith('nf') else ''));meta=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());count=0
  def set_before(ui,sound,machine,values):
   ui.uc.mem_write(sound,bytes(100));ui.uc.mem_write(sound+38,struct.pack('>H',machine*256))
   for sl,value in zip(SLOTS,values):ui.uc.mem_write(sound+20+sl*2,struct.pack('>H',value))
  for old in range(19):
   for new in range(19):
    values=[70*256,91*256,79*256,127*256,88*256,25*256]
    set_before(u,snd,old,values);set_before(r,rs,old,values)
    u.call(0x4001477e,obj,new,0,0);r.call(0x4001477e,ro,new,0,0)
    assert u.uc.mem_read(snd+38,1)[0]==new,(old,new,'machine')
    for i,sl in enumerate(SLOTS):
     actual=struct.unpack('>H',u.uc.mem_read(snd+20+2*sl,2))[0];original=struct.unpack('>H',r.uc.mem_read(rs+20+2*sl,2))[0]
     if old==new or old==17 or new==17 or (i>=2 and (old==6 or new==6)):expected=original
     else:
      desc=u.call(0x4005a692,sl,new);base=meta['tiny_extra']['descriptors']+56*desc;lo,hi=struct.unpack('>ii',u.uc.mem_read(base+8,8));expected=max(lo,min(hi,values[i])) if desc else original
     assert actual==expected,(old,new,sl,actual,expected,original)
    assert not u.bad and not r.bad;count+=1
  # Reset explicite : les valeurs par defaut doivent toujours pouvoir etre chargees.
  for machine in range(19):
   set_before(u,snd,machine,values);set_before(r,rs,machine,values);u.call(0x40014072,obj);r.call(0x40014072,ro);assert bytes(u.uc.mem_read(snd,100))==bytes(r.uc.mem_read(rs,100)),('reset explicite',machine)
  wizard_cases=wizard_roundtrips(stem);all_cases=wizard_control_all(stem)
  reports.append(dict(wizard_native_menu_roundtrips=wizard_cases,wizard_control_all_tracks=all_cases,wizard_modes=7,wizard_tracks=6,wizard_snapshot_lifetime='current MACHINES session',candidate=stem,sha256=meta['sha256'],native_machine_pairs=count,explicit_resets_unchanged=19,bounded_retention=True,midi_and_sample_controls_preserved=True));print('PASS',stem,count,'paires,19resets,42allers-retours Wizard,6pistes ControlAll,retention bornee' ,flush=True)
 (ROOT/('output/firmware/keep-machine-params-proof-'+reports[0]['candidate'].rsplit('-',1)[-1]+'.json')).write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
