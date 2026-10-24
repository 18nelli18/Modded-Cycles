"""Audit prive des 18 machines : froid, regime stable et retrigger separes.
Instructions executees, jamais pourcentages CPU physiques. Notes/137.
Les fichiers/audio sont synthetiques ; vrai update/render et vraie SRAM native.
"""
import argparse,collections,json,math,struct
import numpy as np
from unicorn import UC_HOOK_CODE,m68k_const as C
from test_wizard_playback import fixtures,ROOT
import mcengine as E
import emac
NAMES=['Kick','Snare','Metal','Perc','Tone','Chord','Sample Wizard','SD Vintage','Clap Vintage','SY Toy','SY Bits','SY Swarm','MACRO','ACID','WAVE','TINY','Retrosyn','MIDI Out']
DEFAULT={0:(10,16,16,24),1:(0,127,8,0),2:(46,48,0,20),3:(38,100,64,26),4:(40,38,52,42),5:(3,43,24,64),6:(0,127,127,0),7:(0,110,74,80),8:(24,25,46,37),9:(24,60,110,64),10:(52,102,0,21),11:(20,15,70,127),12:(64,0,64,0),13:(64,64,64,64),14:(0,0,127,0),15:(64,0,64,32),16:(64,0,64,0),17:(0,0,0,0)}
STEM='all-features-polivoks-cpu-trim-test-v26'

def setup_wave(e,frames=4):
 # Format valide du chargeur natif : 4288 mots PCM16 par frame (mipmaps).
 # Stockage et chargement filesystem simules, DSP natif integralement execute.
 from boot_candidate import boot
 _,mem=boot(ROOT/'output/firmware'/(STEM+'.syx'))
 raw=ROOT/'output/wave-audit.bin';raw.write_bytes(mem[0][1][0x79000:0x7a580])
 e.emac.install(emac.disasm(str(raw),0x46779000,0x46779000,0x46779da4))
 n=frames*4288
 e.uc.mem_write(0x48800040,struct.pack('>'+str(n)+'h',*[int(12000*math.sin(i*2*math.pi/256)) for i in range(n)]))
 e.uc.mem_write(0x4677b2a0+20,struct.pack('>I',n))
 e.uc.mem_write(0x4677b2b8+20,struct.pack('>I',0x48800040))

def measure(machine,model=None,controls=None,blocks=12,stem=STEM,modifier=None,stereo=False):
 e=fixtures(stereo,127,0,[stem],native_chordkeys=True)[0]
 e.uc.mem_write(e.audit_symbols['track_slot']+20,struct.pack('>I',0))
 if machine==14:setup_wave(e)
 if modifier:modifier(e)
 c,s,w,ct=controls or DEFAULT[machine]
 if model is not None:s=model
 e.set(5,machine=machine,note=60,pitch=64,color=c,shape=s,sweep=w,contour=ct,decay=100,punch=0)
 table=struct.unpack('>36I',e.uc.mem_read(0x46789048,144))
 assert table[0]==0x400aa08c and table[14]==0x46779000
 up,rnd=table[machine],table[18+machine]
 active=[-1];stage=[None];ret=[0];amount=collections.Counter();bins=collections.Counter();rows=[]
 def trace(u,pc,size,data):
  if pc==e.audit_symbols['sampler_pre']:active[0]=u.reg_read(C.UC_M68K_REG_D2)
  if pc==0x400a7e24:active[0]=-1;stage[0]=None
  if active[0]!=5:return
  if stage[0] and pc==ret[0]:stage[0]=None
  if not stage[0] and pc in (up,rnd):
   stage[0]='update' if pc==up else 'render';ret[0]=int.from_bytes(u.mem_read(u.reg_read(C.UC_M68K_REG_A7),4),'big')
  amount['total']+=1;amount[stage[0] or 'dispatch_amp']+=1;bins[pc&~63]+=1
 e.uc.hook_add(UC_HOOK_CODE,trace)
 error=None
 try:
  for b in range(blocks):
   amount.clear();e.count=0;active[0]=-1;stage[0]=None
   trig=b in (0,blocks-4)
   x=e.block(32 if trig else 0)[5]
   rows.append(dict(block=b,trigger_input=trig,latched_machine=int.from_bytes(e.uc.mem_read(E.VOICE0+5*E.VSTRIDE,4),'big'),instructions=dict(amount),whole_loop=e.count,peak=int(np.max(np.abs(x)))))
 except Exception as ex:error=type(ex).__name__+': '+str(ex)
 # Le trig est consomme au bloc suivant ; le premier bloc est encore KICK.
 valid=[r for r in rows[1:] if r['latched_machine']==machine]
 steady=[r for r in valid if r['block'] not in (1,blocks-3)]
 def stats(seq):
  return {k:dict(mean=sum(r['instructions'].get(k,0) for r in seq)/len(seq),peak=max(r['instructions'].get(k,0) for r in seq)) for k in ('total','update','render','dispatch_amp')} if seq else None
 row=dict(machine=machine,name=NAMES[machine],model=model,parameters=[c,s,w,ct],audible_fixture=max((r['peak'] for r in valid),default=0)>1000,peak=max((r['peak'] for r in valid),default=0),cold=rows[1] if len(rows)>1 else None,steady=stats(steady),retrigger=next((r for r in rows if r['block']==blocks-3),None),hot_64byte_regions=[(hex(at),n) for at,n in bins.most_common(10)],error=error,unmapped=e.unmapped[:4],blocks=rows)
 print('AUDIT',json.dumps({k:v for k,v in row.items() if k not in ('blocks','hot_64byte_regions','cold','retrigger')}),flush=True)
 return row

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--group',choices=['inventory','models','syntakt'],default='inventory');p.add_argument('--stem',default=STEM);a=p.parse_args()
 if a.group=='models':cases=[(12,n,None) for n in range(47)]+[(15,n,None) for n in range(52)]+[(16,n,None) for n in range(6)]
 elif a.group=='syntakt':
  cases=[]
  for m in range(7,12):
   d=DEFAULT[m];cases.append((m,None,d))
   for k in range(4):
    for val in (0,127):
     ctrl=list(d);ctrl[k]=val;cases.append((m,None,tuple(ctrl)))
 else:cases=[(m,None,None) for m in range(18)]
 out=[]
 for m,n,c in cases:
  row=measure(m,n,c,stem=a.stem);out.append(row)
  # Une lacune est inscrite mais ne masque pas les machines suivantes.
  path=ROOT/('output/firmware/all-machines-'+a.stem.rsplit('-',1)[-1]+'-'+a.group+'-cpu-audit.json')
  path.write_text(json.dumps(dict(stem=a.stem,machines=out,limits=['instructions, not hardware cycles/CPU percentages','synthetic assets; mixer/FX/UI/USB/cache and MIDI worker excluded','all listed models at one note/control setting, not every possible parameter','cold first-machine block and retrigger separated; MIDI silent expected']),indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
