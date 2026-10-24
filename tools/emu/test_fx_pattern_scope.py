"""Audit115/121 apres bootstrap : DSP existants et USB preserves.

Les seuls nouveaux chemins audio sont la publication du pattern (copies RAM)
et le gain de sortie WAVE. Fournir les images privees via MC_TEST_STAGING_DIR.
"""
from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from boot_candidate import boot
S=Path(os.environ.get('MC_TEST_STAGING_DIR',R/'output/firmware/staging'))
name='all-features-polivoks-cpu-trim-test-'
m=json.loads((S/(name+'v121.json')).read_text());meta=m['fx_project']
a,am=boot(S/(name+'v115.syx'));b,bm=boot(S/(name+'v121.syx'))
def check(old,new,base,ranges,label):
 delta=[base+i for i,(x,y) in enumerate(zip(old,new)) if x!=y]
 extra=[at for at in delta if not any(start<=at<end for start,end in ranges)]
 assert not extra,(label,[hex(at) for at in extra[:30]])
 print('PASS',label,len(delta),'bytes differ only in the documented hooks and FX storage module',flush=True)
end=0x401aa140-0x40000400
length=0x40195ad8-0x40000400
assert int.from_bytes(b[length:length+4],'big')==meta['end']-0x467ab360
hooks=[(0x40195ad8,4),(0x4005d18a,8),(0x4005d3dc,8),(0x4000f906,6),(0x4005ba0a,8),(0x4005b894,8),(0x400615e8,8),(0x4000fb06,8),(0x4000f872,8),(0x40055c5c,6),(0x4000ec48,6),(0x40010af8,6),(0x40010d10,6),(0x4001199a,6),(0x40011b18,6)]
check(a[:end],b[:end],0x40000400,[(at,at+n) for at,n in hooks],'native OS')
row=m['tiny_extra']['data']+4*(2*m['tiny_extra']['machine_count']+14)
check(am[0][1],bm[0][1],0x46700000,[(meta['code'],meta['code']+meta['code_bytes']),(meta['frame_hook']+2,meta['frame_hook']+6),(row,row+4)]+[(h['at'],h['at']+h['size']) for h in meta['ui_hooks']],'runtime')
print('PASS existing machine/FX renderers, audio IRQ, USB and recovery byte-identical to v115; WAVE gain and pattern publication hooks isolated',flush=True)
