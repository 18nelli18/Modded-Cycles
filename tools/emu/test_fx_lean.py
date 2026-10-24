"""v79/v80 : choix seuls, migrations FX01/CR02, absence des anciens DSP combines."""
import sys,json,struct
from boot_candidate import ROOT
from test_fx_menu_control import fixture
STEM=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v80'

def settings(rev,delay):
 b=bytearray(60);b[:4]=b'FX01';b[4]=rev;b[5:10]=bytes((42,64,24,24,32));b[22:25]=bytes((delay,96,12));b[58:60]=bytes((165,90))
 for i in range(27):b[31+i]=b[4+i]^255
 return bytes(b)

def main():
 m=json.loads((ROOT/'output/firmware'/(STEM+'.json')).read_text());d=m['fx_menu'];assert d['lean_fx'] and d['reverb_selector_order']==[7,3,0,1,2] and d['delay_selector_order']==([5,0,1,2] if d.get('no_shimmer') else [6,5,2,1,0])
 assert not any(k in d['symbols'] for k in ('nd_ap','nd_pitch','nd_clean'))
 assert not any(k in m['delay_crush']['symbols'] for k in ('direct_bus','echo_bus','delay_bus','dg','eg'))
 folder=ROOT/('output/firmware/governor-recovery-'+STEM.rsplit('-',1)[-1]);code=b''.join((folder/n).read_bytes() for n in ('fx.bin','crush.bin','ps1-hot.bin'))
 for text in ((b'SHIMMER 1',) if d.get('no_shimmer') else ())+(b'SHIMMER 2',b'VINYL+REV',b'CHOR1+REV',b'CHOR2+REV',b'CRU1+DEL',b'CRU2+DEL',b'Both 1',b'Both 2'):assert text not in code,text
 revs={0:0,1:1,2:2,3:3,4:3,5:1,6:2,7:7};dels={0:0,1:1,2:2,3:0,4:0,5:5,6:0 if d.get('no_shimmer') else 6,7:0 if d.get('no_shimmer') else 6,8:0}
 if d.get('no_shimmer'):assert not any(k in d['symbols'] for k in ('fx_shift','fx_shift_core','nd_ring','nd_filter','nd_aa','align_heads','nd_offset','ND_AA','ND_HANN'))
 for rev,expected_rev in revs.items():
  for delay,expected_del in dels.items():
   r,s,h,l,files,key,turn,data,bind=fixture(STEM);files['/FxMix.cfg']=settings(rev,delay)
   # Vieille preference Both ne doit pas ecraser FxMix au premier dessin.
   files['/Crush.cfg']=bytes((67,82,48,50,3,96,12,252,159,243,165,90))
   r.call('fx_service');assert r.r32(s['ch_mode'])==expected_rev and r.r32(s['cr_mode'])==expected_del,('migration',rev,delay)
   r.call('cr_service');assert r.r32(s['cr_mode'])==expected_del,('legacy override',delay)
   if rev!=expected_rev or delay!=expected_del:
    saved=files['/FxMix.cfg'];assert (saved[4],saved[22])==(expected_rev,expected_del),('resave',rev,delay)
 print('PASS72 saved-FX migrations, retained IDs unchanged, legacy file priority, stopped-only resave',flush=True)
 # Le transport interdit les E/S de migration.
 r,s,h,l,files,key,turn,data,bind=fixture(STEM);old=settings(5,7);files['/FxMix.cfg']=old;r.w32(0x40a7883c,1);r.call('fx_service');assert files['/FxMix.cfg']==old and r.r32(s['ch_mode'])==0
 print('PASS removed choices, strings and DSP state absent; solo modes only; no settings I/O during playback',flush=True)
 (ROOT/('output/firmware/lean-fx-proof-'+STEM.rsplit('-',1)[-1]+'.json')).write_text(json.dumps({'candidate':STEM,'sha256':m['sha256'],'migration_cases':72,'reverb_modes':d['reverb_selector_order'],'delay_modes':d['delay_selector_order'],'removed_code_and_state':True,'hardware_tested':False},indent=2)+'\n')
if __name__=='__main__':main()
