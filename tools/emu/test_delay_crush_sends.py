"""Envois separes : mixeur/Delay natifs, isolement sixpistes et routes v51."""
import sys,struct,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_wizard_playback import fixtures,ROOT
from test_junior_integration import parts
import mcengine as E,emac
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ

def fresh_fixture(stem):
 e=fixtures(False,127,0,[stem],audit_count=False)[0];u=e.uc;m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());sy=m['delay_crush']['symbols'];u.mem_map(0xfc040000,0x10000)
 for key,binary in [('stereo_chorus','chorus.bin'),('delay_crush','crush.bin')]:
  d=m[key];fn=ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-',1)[-1]+'/'+binary);e.emac.install(emac.disasm(str(fn),d['code'],d['code'],d['code']+d['code_bytes']))
 u.hook_add(UC_HOOK_MEM_READ,lambda uc,a,at,size,v,d:uc.mem_write(at,bytes(size)),begin=0xfc045000,end=0xfc045fff)
 e.call(0x40057260);e.call(0x4005770e);u.mem_write(0x8000b570,struct.pack('>I',0x8000a560));got={};count=[0]
 def obs(uc,pc,*a):
  if pc==0x4005699c:got['send']=bytes(uc.mem_read(0x8000b990,256));count[0]=0
  elif pc==0x400569a2:got['wet']=bytes(uc.mem_read(0x8000ba90,256));got['fx_cost']=count[0]
  elif pc==0x40056b38:got['pre']=bytes(uc.mem_read(0x8000b990,256))
  elif pc==0x40056b42:got['post']=bytes(uc.mem_read(0x8000b990,256));uc.emu_stop()
 u.hook_add(UC_HOOK_CODE,lambda *a:count.__setitem__(0,count[0]+1))
 for at in (0x4005699c,0x400569a2,0x40056b38,0x40056b42):u.hook_add(UC_HOOK_CODE,obs,begin=at,end=at)
 return e,m,sy,got

# Trois instances natives par image, retour a leur etat initial entre cas.
# Pas de DSP remplace : memoire SRAM/FX/globaux et contexte CPU restaures.
POOLS={};CURSORS={}
def fixture(stem):
 pool=POOLS.setdefault(stem,[]);index=CURSORS.get(stem,0)%3;CURSORS[stem]=index+1
 if index>=len(pool):
  f=fresh_fixture(stem);e=f[0]
  regions=[(0x80000000,0x20000),(0x46700000,0x100000),(0x40a70000,0x20000),(0x40700000,0x1000),(0xfc040000,0x10000)]
  saved=[(at,bytes(e.uc.mem_read(at,n))) for at,n in regions];pool.append((f,saved,e.uc.context_save(),list(e.emac.acc),e.emac.macsr,e.emac.mask))
 f,saved,cpu,acc,macsr,mask=pool[index];e=f[0]
 for at,raw in saved:e.uc.mem_write(at,raw)
 e.uc.context_restore(cpu);e.emac.acc[:]=acc;e.emac.macsr=macsr;e.emac.mask=mask;e.unmapped.clear();f[3].clear()
 return f

def setup(f,mode,delays,crushes,pan=64,tracks=(0,)):
 e,m,sy,g=f;u=e.uc;raw=bytearray(440)
 for t in range(6):
  struct.pack_into('>H',raw,2*t,32512 if t in tracks else 0)
  for slot,v in [(19,32512),(20,delays[t]*256),(21,0),(22,pan*256)]:struct.pack_into('>H',raw,14+66*t+2*slot,v)
 struct.pack_into('>4H',raw,428,11000,0,10752,16384);u.mem_write(E.PARAMS,bytes(raw))
 samples=[round(180000000*math.sin(i*math.pi/7+t)) if t in tracks else 0 for t in range(6) for i in range(32)];u.mem_write(E.TRACK_BASE,struct.pack('>192i',*samples))
 u.mem_write(sy['cr_state'],struct.pack('>5I',1,mode,256,256,0)+bytes(304));u.mem_write(sy['cr_mode'],struct.pack('>I',mode));u.mem_write(sy['cr_rate'],struct.pack('>I',96));u.mem_write(sy['cr_bits'],struct.pack('>I',3))
 if 'cr_send' in sy:u.mem_write(sy['cr_send'],struct.pack('>6I',*crushes))

def run(f,n=3):
 e,m,sy,g=f
 for _ in range(n):e.uc.mem_write(0x8000a560,bytes(544));e.call(0x400567ba,0,E.PARAMS)
 assert not e.unmapped
 return dict(g)

def main():
 proof=ROOT/'output/firmware/crush-send-proof-v53.json';reports=json.loads(proof.read_text()) if proof.exists() else []
 for stem in sys.argv[1:]:
  cases=0;costs={};previous=stem.rsplit('-',1)[0]+'-'+('v51nf' if stem.endswith('nf') else 'v51')
  for mode in (0,1,2):
   fs=[fixture(previous),fixture(stem)]
   for f in fs:setup(f,mode,[77]*6,[0]*6,tracks=tuple(range(6)))
   for b in range(3):
    a,z=[run(f,1) for f in fs];assert a['post']==z['post'] and a['wet']==z['wet'],('legacy',mode,b)
   costs[str(mode)]=z['fx_cost'];cases+=1
  for mode in (3,4):
   for delay,pan in ((0,0),(64,64),(127,127)):
    fs=[fixture(stem),fixture(stem)]
    for f,mo in zip(fs,(0,mode)):setup(f,mo,[delay]*6,[0]*6,pan)
    a,z=[run(f) for f in fs];assert a['send']==z['send'] and a['wet']==z['wet'],('clean wet',mode,delay,pan)
    assert max(abs(x-y) for x,y in zip(struct.unpack('>64i',a['post']),struct.unpack('>64i',z['post'])))<2048,('clean Q20 rounding',mode,delay,pan)
    costs[str(mode)+'-zero']=z['fx_cost'];cases+=1;print('PASS clean',mode,delay,pan,flush=True)
  print('PASS Delay/Crush1/Crush2 exacts v51 ; Both1/2 crusher0 = Delay natif',stem,flush=True)
  for track in range(6):
   fs=[fixture(stem),fixture(stem),fixture(stem)]
   for f,mode in zip(fs,(0,3,4)):setup(f,mode,[0]*6,[127 if i==track else 0 for i in range(6)],tracks=(track,))
   clean,b1,b2=[run(f) for f in fs];assert clean['post']==b1['post'];assert b2['post']!=clean['post'];assert not any(b2['wet']);assert not any(b1['wet']);assert b2['post']!=bytes(256)
   costs['Both2-direct']=b2['fx_cost'];cases+=1
  for mode in (3,4):
   fs=[fixture(stem),fixture(stem)]
   for f,cs in zip(fs,([0]*6,[127,0,0,0,0,0])):setup(f,mode,[0,127,0,0,0,0],cs,tracks=(0,1))
   a,z=[run(f) for f in fs];assert a['send']==z['send'] and a['wet']==z['wet'];assert (a['post']==z['post'])==(mode==3);cases+=1
  fs=[fixture(stem),fixture(stem)]
  for f,cs in zip(fs,([0]*6,[127]*6)):setup(f,3,[127]*6,cs,tracks=tuple(range(6)))
  a,z=[run(f) for f in fs];assert a['send']==z['send'];assert bytes(fs[0][0].uc.mem_read(0x8000a560,256))!=bytes(fs[1][0].uc.mem_read(0x8000a560,256));costs['Both1-full']=z['fx_cost'];cases+=1
  setup(fs[1],4,[127]*6,[127]*6,tracks=tuple(range(6)));z=run(fs[1]);costs['Both2-full']=z['fx_cost']
  f=fs[1]
  for mode in (0,4,3,2,1,4,0):
   f[0].uc.mem_write(f[2]['cr_mode'],struct.pack('>I',mode))
   # Le fondu est dans cr_process : vrai DSP, hors preparation DMA du mixeur.
   for _ in range(70):f[0].call(f[2]['cr_process'],0x40711000,0x40712000,0x40713000)
   assert struct.unpack('>4I',f[0].uc.mem_read(f[2]['cr_state'],16))==(1,mode,256,256)
  old,new=parts(previous),parts(stem);assert old[2]==new[2]
  for sec in old[0]['sections']:
   if sec['id']==3:continue
   other=next(s for s in new[0]['sections'] if s['id']==sec['id']);assert old[0]['blob'][sec['off']:sec['off']+sec['size']]==new[0]['blob'][other['off']:other['off']+other['size']]
  reports=[x for x in reports if x["candidate"]!=stem];reports.append(dict(candidate=stem,sha256=f[1]['sha256'],native_mixer_cases=cases,legacy_routes_exact=True,zero_crusher_clean_delay=True,per_track_isolation=True,direct_without_delay=True,mode_fades=True,fx_instruction_counts=costs,hardware_cpu_percent=None));print('PASS',cases,'mixeur natif,6pistes,isolement,direct,transitions ; cout instructions',costs,flush=True);proof.write_text(json.dumps(reports,indent=2)+'\n')
 (ROOT/'output/firmware/crush-send-proof-v53.json').write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
