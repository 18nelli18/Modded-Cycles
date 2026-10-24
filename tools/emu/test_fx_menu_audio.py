"""FX v55 dans le mixeur natif : dry Vinyl0, sends independants et reverb v54 exacte."""
import sys,json,struct,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_delay_crush_sends import fresh_fixture,setup,run
from boot_candidate import ROOT
from unicorn import UC_HOOK_CODE,m68k_const as C
import emac
import mcengine as E
POOLS={}
def fixture(stem,index):
 pool=POOLS.setdefault(stem,{})
 if index not in pool:
  f=fresh_fixture(stem);e,m,sy,got=f
  if m.get('fx_menu'):
   d=m['fx_menu'];p=ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-',1)[-1]+'/fx.bin');e.emac.install(emac.disasm(str(p),d['code'],d['code'],d['code']+d['code_bytes']))
   if d.get('ps1_fast_opt'):
    at=d['ps1_hot_address'];e.emac.install(emac.disasm(str(p.with_name('ps1-hot.bin')),at,at,at+d['ps1_hot_code_bytes']))
  if m.get('fx_menu'):
   def capture(uc,pc,*args):
    if pc==0x40056a2c:got['rev_input']=bytes(uc.mem_read(0x8000b990,256))
    else:got['rev_wet']=bytes(uc.mem_read(0x8000bb90,256))
   for at in (0x40056a2c,0x40056a32):e.uc.hook_add(UC_HOOK_CODE,capture,begin=at,end=at)
  regions=[(0x80000000,0x20000),(0x46700000,0x200000 if m.get('fx_menu') else 0x100000),(0x40a70000,0x20000),(0x40700000,0x20000),(0xfc040000,0x10000)]
  saved=[(a,bytes(e.uc.mem_read(a,n))) for a,n in regions];pool[index]=(f,saved,e.uc.context_save(),list(e.emac.acc),e.emac.macsr,e.emac.mask)
 f,saved,cpu,acc,macsr,mask=pool[index];e=f[0]
 for a,raw in saved:e.uc.mem_write(a,raw)
 e.uc.context_restore(cpu);e.emac.acc[:]=acc;e.emac.macsr=macsr;e.emac.mask=mask;e.unmapped.clear();f[3].clear();return f

def configure(f,mode,sends,aux=0,cr=0):
 setup(f,cr,[0]*6,[0]*6,tracks=(0,));e,m,sy,got=f;u=e.uc
 for t in range(6):u.mem_write(E.PARAMS+56+66*t,struct.pack('>H',sends[t]*256))
 if m.get('fx_menu'):
  s=m['fx_menu']['symbols']
  for name,value in [('ch_mode',mode),('active',mode),('ready',1),('gain',256),('prior_gain',256),('fx_crackle',0),('fx_warble',80),('fx_wspeed',40)]:u.mem_write(s[name],struct.pack('>I',value))
  for name in ('fx_aux_ch','fx_aux_vi'):u.mem_write(s[name],struct.pack('>6I',aux,0,0,0,0,0))

def main():
 reports=[]
 for stem in sys.argv[1:]:
  old=stem.replace('v55','v54');a=fixture(old,0);b=fixture(stem,0)
  for f in (a,b):configure(f,0,[100,0,0,0,0,0])
  for i in range(3):
   x,y=[run(f,1) for f in (a,b)];assert x['post']==y['post'] and x['wet']==y['wet'],('native reverb regression',i)
  print('PASS native full-mixer Reverb samples exact v54',stem,flush=True)
  costs={}
  for mode in (1,2,3,4,5,6):
   a=fixture(stem,0);b=fixture(stem,1);configure(a,0,[0]*6);configure(b,mode,[127 if mode in (1,2,3) else 0,0,0,0,0,0],127)
   x,y=[run(f,3) for f in (a,b)]
   if mode in (3,4):assert x['post']!=y['post'] and y['post']!=bytes(256),('vinyl not wet',mode)
   if mode in (1,2,5,6):
    # Remplir les retards chorus sans rerendre toutes les voix.
    e,m,sy,got=b;s=m['fx_menu']['symbols']
    e.uc.mem_write(0x40710800,y['rev_input'])
    for _ in range(24):e.call(s['fx_reverb'],0x40710200,0x40710800,E.PARAMS+432,E.PARAMS,0x40708000,0x40708020)
    assert any(e.uc.mem_read(0x40710200,256)),('chorus wet silent',mode)
   costs[str(mode)]=y['fx_cost']
  print('PASS all six added/combined modes execute native mixer with signal',stem,flush=True)
  # Vinyl zero : aucun signal dans le bus, dry exact y compris apres des sends non nuls.
  a=fixture(stem,0);b=fixture(stem,1);configure(a,0,[0]*6);configure(b,3,[0]*6)
  for _ in range(3):
   x,y=[run(f,1) for f in (a,b)];assert x['post']==y['post'] and not any(y['wet']), 'Vinyl send0 not dry'
  # Aux chorus/Vinyl0 : retour reverb inchangé ; bus propres par piste.
  for mode in (4,5,6):
   a=fixture(stem,0);b=fixture(stem,1);configure(a,0,[90,0,0,0,0,0]);configure(b,mode,[90,0,0,0,0,0],0)
   for _ in range(3):
    x,y=[run(f,1) for f in (a,b)];assert x['post']==y['post'],('combined aux0 changes reverb',mode)
  # Vinyl independant de reverb et d'une piste silencieuse.
  a=fixture(stem,0);b=fixture(stem,1);configure(a,4,[0]*6,0);configure(b,4,[0]*6,0);s=b[1]['fx_menu']['symbols'];b[0].uc.mem_write(s['fx_aux_vi']+4,struct.pack('>I',127))
  x,y=[run(f,3) for f in (a,b)];assert x['post']==y['post'],'silent track leaks into vinyl'
  print('PASS Vinyl send0 exact dry; all combined aux0 exact Reverb; silent-track isolation',stem,flush=True)
  # DSP vinyl complet, bornes et silence apres excitation ; aucune allocation.
  f=fixture(stem,0);e,m,sy,g=f;s=m['fx_menu']['symbols'];inp,out=0x40710000,0x40710200;tone=struct.pack('>64i',*[int(180000000*math.sin(i/4)) for i in range(64)])
  hashes=[]
  for crack,amt,speed in [(0,0,0),(127,0,0),(0,127,0),(0,127,127),(127,127,127)]:
   e.call(s['fx_vinyl_reset'])
   for name,val in [('fx_crackle',crack),('fx_warble',amt),('fx_wspeed',speed)]:e.uc.mem_write(s[name],struct.pack('>I',val))
   result=b''
   for i in range(32):e.uc.mem_write(inp,tone);e.call(s['fx_vinyl'],out,inp);result+=bytes(e.uc.mem_read(out,256))
   hashes.append(__import__('hashlib').sha256(result).hexdigest())
   if not crack and not amt:assert result==struct.pack('>64i',*[(v>>11)*2048 for v in struct.unpack('>64i',tone)])*32,'zero vinyl controls not transparent'
  assert len(set(hashes))==5,'vinyl controls have no audible effect'
  e.uc.mem_write(inp,bytes(256))
  for _ in range(96):e.call(s['fx_vinyl'],out,inp)
  assert not any(e.uc.mem_read(out,256)) and not e.unmapped
  print('PASS Vinyl crackle/warble amount/speed affect PCM, transparent controls0, excited tail returns to exact silence',stem,flush=True)
  reports.append(dict(stem=stem,sha256=m['sha256'],base='v54',native_reverb_exact=True,vinyl_send_zero_dry=True,combined_aux_zero_exact=True,vinyl_parameter_pcm_hashes=hashes,hardware_cpu_percent=None))
 proof=ROOT/'output/firmware/fx-menu-audio-proof-v55.json';prior=json.loads(proof.read_text()) if proof.exists() else [];reports=[x for x in prior if x['stem'] not in sys.argv[1:]]+reports;proof.write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
