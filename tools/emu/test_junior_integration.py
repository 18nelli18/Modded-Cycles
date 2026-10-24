"""Integration privee Junior : seuls index16 et ses descripteurs changent.
Verifie les octets des autres moteurs, ABI et reponse des potards dans l'OS.
"""
import argparse,json,struct,sys,hashlib
from pathlib import Path
import numpy as np
from unicorn import m68k_const as C
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_wizard_playback import fixtures,ROOT
from gen_governor_recovery_test import read,BASE,START,TAIL,RUNTIME
import mcengine as E
from mtlib import aplib

def parts(stem):
 _,p,im,_=read(ROOT/'output/firmware'/(stem+'.syx'));end=int.from_bytes(im[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 b=im[START:end];rt,_=aplib.depack(struct.pack('>II',len(b),sum(b)&0xffffffff)+b)
 return p,im[:START],rt,im[end:]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate');a=p.parse_args();nf=a.candidate.endswith('nf')
 base='no-filter-wizard-polivoks-cpu-trim-test-v33nf' if nf else 'all-features-polivoks-cpu-trim-test-v33'
 old=parts(base);new=parts(a.candidate);m=json.loads((ROOT/'output/firmware'/(a.candidate+'.json')).read_text());sy=m['junior']['symbols']
 allowed=set()
 for at,n in [(0x46789088,4),(0x467890d0,4),(0x46789040,4),(0x4678ae78,56*5)]:allowed.update(range(at-RUNTIME,at-RUNTIME+n))
 assert len(old[2])==len(new[2]) and {i for i,(x,y) in enumerate(zip(old[2],new[2])) if x!=y}<=allowed
 allowed=set()
 for at,n in [(0x40195ad0,4),(0x40195ad8,4)]:allowed.update(range(at-BASE,at-BASE+n))
 assert {i for i,(x,y) in enumerate(zip(old[1],new[1])) if x!=y}<=allowed
 allowed=set()
 for table in ('identity_stats','identity_icons'):
  off=m[table]+10*28-TAIL;ptr=int.from_bytes(new[3][off+16:off+20],'big');allowed.update(range(ptr-TAIL,ptr-TAIL+512))
 assert {i for i,(x,y) in enumerate(zip(old[3],new[3])) if x!=y}<=allowed
 for s in old[0]['sections']:
  if s['id']==3:continue
  t=next(t for t in new[0]['sections'] if t['id']==s['id'])
  assert old[0]['blob'][s['off']:s['off']+s['size']]==new[0]['blob'][t['off']:t['off']+t['size']]
 e=fixtures(False,127,0,[a.candidate],native_chordkeys=True)[0]
 for k,label in enumerate(['Wave','Warp','Noise','Motion','Decay']):
  raw=e.uc.mem_read(0x4678ae78+56*k,56);assert struct.unpack_from('>3I',raw,8)==(0,32512,(50 if k==4 else 0)<<8)
  for off,text in [(44,label),(52,['WAVE','WARP','NOIS','MOTN','DEC'][k])]:
   ptr=struct.unpack_from('>I',raw,off)[0];assert bytes(e.uc.mem_read(ptr,len(text)+1))==text.encode()+b'\0'
 print('PASS seuls pointeurs/UI index16 et deux bitmaps changent ; autres moteurs/Feral/CPUfixes exacts, bootloader/updater exacts, labels/ranges natifs corrects',flush=True)
 # Vraie preparation OS, update/render ; registres callee-save sentinelles.
 v=E.VOICE0+5*E.VSTRIDE;param=E.PARAMS+14+66*5;out=E.TRACK_BASE+128*5
 regs={getattr(C,'UC_M68K_REG_'+r+str(i)):0x12340000+i for r,ix in [('D',range(2,8)),('A',range(2,7))] for i in ix}
 hashes={}
 for name,kw in [('base',{}),('Wave',dict(color=64)),('Warp',dict(shape=30)),('Noise',dict(sweep=127)),('Motion',dict(contour=79)),('Pitch',dict(pitch=76)),('Fine',dict(finetune=127)),('Punch',dict(punch=1)),('Decay',dict(decay=20)),('Gate',dict(gate=1))]:
  e.call(E.VOICE_RESET,v);e.uc.mem_write(v,struct.pack('>II',16,16));e.set(5,machine=16,note=60,pitch=64,color=0,shape=0,sweep=0,contour=0,punch=0,finetune=64,decay=100,gate=0);e.set(5,**kw);audio=b''
  for b in range(32):
   e._write_params();e.emac.macsr=0xa0
   for ac in range(4):e.emac.put_physical(ac,0)
   for off,val in [(0x34,int(b==0)),(0x38,int(b==1)),(0x3c,int(b==12)),(0x24c,e.trk[5]['gate']*256)]:e.uc.mem_write(v+off,struct.pack('>I',val))
   e.call(0x400a7d16,v)
   for at,args in [(sy['junior_update'],(60<<16,v,param)),(sy['junior_render'],(out,v))]:
    for reg,val in regs.items():e.uc.reg_write(reg,val)
    e.call(at,*args)
    assert all(e.uc.reg_read(reg)==val for reg,val in regs.items()),('ABI',name,hex(at))
   audio+=bytes(e.uc.mem_read(out,128))
  hashes[name]=hashlib.sha256(audio).hexdigest();assert any(audio),name
 for k,h in hashes.items():
  if k!='base':assert h!=hashes['base'],('inactive parameter',k)
 print('PASS Wave/Warp/Noise/Motion/Pitch/Fine/Punch/Decay/Gate influencent le vrai PCM ; trigs/release et ABI preserves',flush=True)
 for t in range(6):e.set(t,machine=16,note=36+t*7,color=t*20,shape=t*25,sweep=t*25,contour=127,punch=t%2,decay=100,gate=0)
 peaks=np.zeros(6,dtype=np.int64)
 for b in range(48):
  x=e.block(63 if b%8==0 else 0,63 if b%8==6 else 0);peaks=np.maximum(peaks,np.max(np.abs(x),axis=1))
 assert all(peaks>1000) and max(peaks)<2147483647 and not e.unmapped,peaks
 print('PASS48 blocs sixJUNIOR, notes/warps/noise/glitch/unison distincts, release/retrigger, aucun acces non mappe',peaks.tolist(),flush=True)
 (ROOT/('output/firmware/junior-integration-proof-'+a.candidate.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(dict(candidate=a.candidate,sha256=m['sha256'],other_engine_bytes_exact=True,sections_other_than_main_exact=True,parameter_hashes=hashes,peaks=peaks.tolist()),indent=2)+'\n')
if __name__=='__main__':main()
