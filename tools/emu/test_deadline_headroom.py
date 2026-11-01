"""Avant/apres reel : pic sous deadline sans vol, surcharge/soutenu inchanges."""
from pathlib import Path
src=Path(__file__).with_name('test_complete_irq_accounting.py').read_text().split('rows=[]')[0]
exec(compile(src,__file__,'exec'))
ph=m['deadline_headroom'];entry=ph['hook'];patched=bytes(r.u.mem_read(entry,8));original=bytes.fromhex(ph['original_prefix']);assert patched[-2:]==b'\x4e\x71'
rows=[];scenarios=[('soft93',80,93,93,True,False),('soft98',80,98,98,True,False),('reserve99',80,99,99,True,ph['relief_threshold_q']<=253),('reported81_99',81,99,99,True,ph['relief_threshold_q']<=253),('deadline100',75,99,100,True,True),('overrun108',75,98,108,True,True),('sustained90',90,90,90,True,True),('sustained86_peak98',86,98,98,True,True),('isolated108',60,70,108,False,False),('normal75',60,75,75,False,False)]
for name,initial,previous,current,before_expected,after_expected in scenarios:
 states=[];fades=[]
 for code in (original,patched):
  r.u.mem_write(entry,code);r.u.ctl_remove_cache(entry,entry+64);setup(r,m,[0,4,4,2,0,5]);q=initial*256//100
  for off,value in [(0x78,q),(0xf10,q*8),(0xf14,q*256),(0xf04,previous*256//100)]:r.w32(GB+off,value)
  r.u.mem_write(0x80001858+4*128,struct.pack('>32i',*([100000000]*32)));start=1000000;r.w32(GB+0x80,start);r.w32(GB+0xf00,start-NOM);r.w32(0xfc07000c,start+NOM*current//100);r.call(ps['mf_old_audio_end']);fades.append(list(r.u.mem_read(GB+0x58,6)));states.append(bytes(r.u.mem_read(GB,0x1200)))
 assert bool(any(fades[0]))==before_expected and bool(any(fades[1]))==after_expected,(name,fades)
 if before_expected==after_expected:assert states[0]==states[1],('unchanged state',name)
 else:assert fades[0][4] and not any(fades[1]),('track5',name,fades)
 rows.append(dict(case=name,old=fades[0],new=fades[1]));print('PASS',rows[-1],flush=True)
# Frontiere exacte de la reserve : garder la charge en q8 sans arrondi en pourcent.
for current_q in (252,253,254,255,256):
 outcomes=[]
 for code in (original,patched):
  r.u.mem_write(entry,code);r.u.ctl_remove_cache(entry,entry+64);setup(r,m,[0,4,4,2,0,5]);q=80*256//100
  for off,value in [(0x78,q),(0xf10,q*8),(0xf14,q*256),(0xf04,250)]:r.w32(GB+off,value)
  r.w32(GB+0x80,1000000);r.w32(GB+0xf00,1000000-NOM);r.w32(0xfc07000c,1000000+current_q*(NOM//256));r.call(ps['mf_old_audio_end']);assert r.r32(GB+0x7c)==current_q
  outcomes.append(bytes(r.u.mem_read(GB,0x1200)))
 assert any(outcomes[0][0x58:0x5e])
 if current_q<ph['relief_threshold_q']:assert not any(outcomes[1][0x58:0x5e])
 else:assert outcomes[0]==outcomes[1]
print('PASS exact reserve frontier',ph['relief_threshold_q'],'and actual deadline q256',flush=True)
r.u.mem_write(entry,patched);r.u.ctl_remove_cache(entry,entry+64)
# Une charge presque pleine persistante ne reste pas exemptee : le soutenu intervient.
setup(r,m,[0,4,4,2,0,5]);q=60*256//100
for off,value in [(0x78,q),(0xf10,q*8),(0xf14,q*256),(0xf04,q)]:r.w32(GB+off,value)
first=None
for i in range(450):
 start=1000000+i*NOM;r.w32(GB+0x80,start);r.w32(GB+0xf00,start-NOM);r.w32(0xfc07000c,start+NOM*98//100);r.call(ps['mf_old_audio_end'])
 if any(r.u.mem_read(GB+0x58,6)):first=i;break
assert first is not None and first<450,first
print('PASS sustained98 eventually invokes relief, first block',first,flush=True)
a.output.write_text(json.dumps(dict(cases=rows,sustained98_first_fade_block=first,synthetic_load=True,hardware_tested=False),indent=2)+'\n')
