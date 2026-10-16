"""Note 103 : vrai boot, callback effectivement raccorde, DATA et frontieres B.
Les peripheriques, objets UI exterieurs et hooks de chance sont simules.
"""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,STACK,STOP,OBJ
from test_sdvintage import main_os_from_syx
import build
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args();prefix=pathlib.Path(a.case)
 cat=json.loads(prefix.with_suffix('.json').read_text())['tweaks'];sg=next(t for t in cat if t.get('symbols',{}).get('sg_q_hook'));bank=next((t for t in cat if t['id']=='midi-out-bank'),None)
 img=main_os_from_syx(str(prefix.with_suffix('.syx')));r=Rig(img,{'writes':[]},{'writes':[],'symbols':sg['symbols']});u=r.u;bs={k:int(v,16) for k,v in bank['symbols'].items()} if bank else {}
 for at,n in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:u.mem_map(at,n)
 def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
 sites=set()
 for at,raw in [(build.BASE,img)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for t in cat if t.get('append') for p in t['append']['parts'] if 'hex' in p]:sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
 for at in sites:u.hook_add(UC_HOOK_CODE,cache,begin=at,end=at)
 u.reg_write(mk.UC_M68K_REG_A7,STACK);u.mem_write(STACK,struct.pack('>I',STOP));u.emu_start(0x40000530,0x4000053a,count=200_000_000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a;r.call(0x4007929c)
 if bank:
  for part in bank['append']['parts']:
   if 'hex' in part:
    at=int(part['dest'],16);raw=bytes.fromhex(part['hex']);assert bytes(u.mem_read(at,len(raw)))==raw,'code altere par boot/cache'
 renderer=bs['sg_render'] if bank else r.s['sg_render']
 r.w32(r.s['sg_intro'],0);r.w32(r.s['sg_obj'],OBJ);r.w32(r.s['sg_row'],1)
 for side in (['A','B'] if bank else ['A']):
  if bank:r.w32(bs['ml_genie_b_owner'],OBJ if side=='B' else 0)
  for mode,label in [(0,'Loop'),(1,'Page')]:
   r.w32(0x4015fb80,mode);r.texts.clear();r.call(renderer,OBJ,0x93006000)
   labels=[t[2] for t in r.texts]
   if a.baseline and bank:assert 'Sound' in labels and str(mode) in labels,labels
   else:assert any(x in labels for x in ['Queue','Queue at']) and label in labels and 'Sound' not in labels,labels
   print('PASS callback reel',side,mode,labels,flush=True)
 if a.baseline:return
 # DATA et bornes du champ reel, sans remplacer son setter.
 r.w32(0x4015fb80,0);r.w32(r.s['sg_edit'],0);r.click();r.knob(1);assert r.r32(0x4015fb80)==1;r.knob(1);assert r.r32(0x4015fb80)==1;r.knob(-1);assert r.r32(0x4015fb80)==0;r.knob(-1);assert r.r32(0x4015fb80)==0;r.click()
 print('PASS vrai DATA : Loop/Page, bornes 0/1',flush=True)
 if not bank:return
 # Le commit copie/compare vraiment la voie ; seuls les locks chance sont isoles.
 for name,value in [('ml_gc_validate',1),('ml_gc_apply',0),('ml_gc_save_undo',0)]:
  if name in bs:r.stubs[bs[name]]=lambda args,value=value:value;u.hook_add(UC_HOOK_CODE,r.stub,begin=bs[name],end=bs[name])
 lane=0x93070000
 for length in (16,20,32,48,64):
  for mode in (0,1):
   for step in range(length):
    before=bytes([1,0,6,4,length,2,0,0])+bytes([60,100,1,3])*64;after=before[:8]+bytes([72,100,1,3])*64
    u.mem_write(lane,before);u.mem_write(bs['ml_gq_before'],before);u.mem_write(bs['ml_gq_after'],after)
    r.w32(bs['ml_gq_state'],1);r.w32(bs['ml_gq_lane'],lane);r.w32(bs['ml_gq_track'],3);r.w32(bs['ml_gq_kind'],0);r.w32(0x4015fb80,mode)
    u.reg_write(mk.UC_M68K_REG_A0,lane);u.reg_write(mk.UC_M68K_REG_D0,3);u.reg_write(mk.UC_M68K_REG_D1,step);r.call(bs['ml_genie_boundary'])
    expected=step==0 or mode==1 and step%16==0
    assert r.r32(bs['ml_gq_state'])==(0 if expected else 1),(length,mode,step)
    assert bytes(u.mem_read(lane,264))==(after if expected else before)
    assert u.reg_read(mk.UC_M68K_REG_D1)==step
 print('PASS B : toutes frontieres 16/20/32/48/64, aucun commit precoce, D1/pile preserves',flush=True)
if __name__=='__main__':main()
