"""Chord courant contre cache par piste : etat DSP exact, six pistes, cout compte.
Les getters des reglages sont instrumentes, pas le DSP ni le voicing natif.
"""
import pathlib,sys,struct,random,json,os
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
import mcengine as E
from unicorn import UC_HOOK_CODE,m68k_const as mk

def load(case):
 img,mem,ts=boot_case(case);start=min(a for a,b in mem);end=max(a+len(b) for a,b in mem);raw=bytearray(end-start)
 for a,b in mem:raw[a-start:a-start+len(b)]=b
 e=E.Engine(img,extra_code=[(0x40100000,0x100000)],payload=(start,bytes(raw)))
 engine=next(t for t in ts if t.get('gov'));blob=next(b for a,b in mem if a==int(engine['append']['dest'],16))
 for off,at,size in [(0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)]:e.uc.mem_write(at,blob[off:off+size])
 ck=next(t for t in ts if t['id']=='chord-keys-supermodel');sy={k:int(v,16) for k,v in ck['symbols'].items()};e.cfg=[0]*6;e.controls=[0]*6;e.count=0
 def stub(at,fn):
  def hook(u,pc,size,data):
   sp=u.reg_read(mk.UC_M68K_REG_A7);ret,lane=struct.unpack('>II',u.mem_read(sp,8));u.reg_write(mk.UC_M68K_REG_D0,fn(lane));u.reg_write(mk.UC_M68K_REG_PC,ret);u.reg_write(mk.UC_M68K_REG_A7,sp+4)
  e.uc.hook_add(UC_HOOK_CODE,hook,begin=at,end=at)
 stub(sy['ck_audio_config'],lambda lane:e.cfg[lane]);stub(sy['ck_audio_locked_controls'],lambda lane:e.controls[lane])
 def counter(u,pc,size,data):e.count+=1
 e.uc.hook_add(UC_HOOK_CODE,counter)
 return e,sy

def main():
 rigs=[load('build/cut-endpoint/usb'),load(os.environ.get('MIDI_SAFETY_CASE','build/midi-safety/usb'))];rng=random.Random(139);cost={'off':[0,0],'hit':[0,0],'miss':[0,0]};last=None
 # Chaque configuration est executee trois fois pour couvrir miss puis hits.
 for case in range(240):
  lane=case%6;enabled=case%4!=0;mode=case%7;root=48;note=rng.randrange(36,97);color=rng.randrange(128);shape=rng.randrange(33);controls=(case%7)<<8
  cfg=(int(enabled)<<31)|(mode<<28)|(root<<21)|sum((case%5)<<(3*i) for i in range(7))
  for repeat in range(3):
   outs=[]
   for j,(e,sy) in enumerate(rigs):
    e.cfg[lane]=cfg;e.controls[lane]=controls;e.machine_defaults(lane,'CHORD');e.set(lane,note=note,shape=shape,color=color,pitch=64,finetune=64);e._write_params();p=E.PARAMS+14+lane*66;voice=E.VOICE0+lane*E.VSTRIDE
    before=bytes(e.uc.mem_read(p,66));e.emac.macsr=0xa0;e.count=0;e.call(0x400aae88,note<<16,voice,p)
    assert bytes(e.uc.mem_read(p,66))==before
    outs.append((bytes(e.uc.mem_read(voice,E.VSTRIDE)),bytes(e.uc.mem_read(sy['ck_chord_live']+4*lane,4))))
    kind='off' if not enabled else 'miss' if repeat==0 else 'hit';cost[kind][j]+=e.count
   assert outs[0]==outs[1],(case,repeat,lane,enabled,mode,note,color,shape)
 print('PASS 720updates natifs : etats complets et noms exacts, six pistes, sept gammes, extensions/palettes/dispositions/gestes, changements et hits')
 for kind,(old,new) in cost.items():print(kind,'instructions',old,new,'variation',round(100*(new-old)/old,2),'% (pas cycles hardware)')
 assert cost['off'][1]<cost['off'][0] and cost['hit'][1]<cost['hit'][0]
 pathlib.Path('build/midi-safety/chord-proof.json').write_text(json.dumps(cost,indent=2)+'\n')
if __name__=='__main__':main()
