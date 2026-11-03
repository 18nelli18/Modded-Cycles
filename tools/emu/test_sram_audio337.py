"""Relocation SRAM : verifier les noyaux complets, pas seulement les copies.

--part hall/post/filter execute les preuves existantes contre les nouvelles
adresses. Les autres etats, gains et echantillons doivent rester identiques.
"""
from pathlib import Path
import sys
part=sys.argv[sys.argv.index('--part')+1];i=sys.argv.index('--part');del sys.argv[i:i+2]
assert part in ('hall','post','filter','delay','chord')
if part!='hall' and '--capture' in sys.argv:
 i=sys.argv.index('--capture');del sys.argv[i:i+2]
if part=='hall':
 source=Path(__file__).with_name('test_hall_ramp322.py').read_text()
 old="new=bytearray(old);d=hall_ramp322.apply(m,new,a.output.parent/'module',opt=os.environ.get('SM_HALL_OPT','-O3'));fs=m['fx_menu']['symbols'];entry=d['symbols']['fx_hall'];rigs=[]"
 new="""new=bytearray(old);native_new=bytearray(native);sram_old=(a.capture/'sram.bin').read_bytes();sram_new=bytearray(sram_old)
from sram_audio337 import apply as sram_apply
sr=sram_apply(m,native_new,new,sram_new,a.output.parent/'module');d=sr;fs=m['fx_menu']['symbols'];entry=fs['fx_hall'];rigs=[]"""
 assert old in source;source=source.replace(old,new)
 source=source.replace("r=Rig(native,", "r=Rig(bytes(native_new) if blob is new else native,")
 source=source.replace("rigs.append(r)", "r.u.mem_map(0x80000000,0x10000);r.u.mem_write(0x80000000,bytes(sram_new) if blob is new else sram_old);rigs.append(r)")
 source=source.replace("assert any(row['saved']>0 for row in rows)", "assert sr['SRAM_used']<=sr['SRAM_reclaimed']")
 source=source.replace('HALL blocks','SRAM HALL blocks')
else:
 name={'post':'test_post_static314.py','filter':'test_filter_unroll308.py','delay':'test_delay_static307.py','chord':'test_chord_second308.py'}[part];source=Path(__file__).with_name(name).read_text()
 common="""from sram_audio337 import apply as sram_apply
native=bytearray(e.uc.mem_read(0x40000400,0x1ffc00));runtime=bytearray(e.uc.mem_read(0x46700000,0x300000));sram=bytearray(e.uc.mem_read(0x80000000,65536))
sr=sram_apply(meta,native,runtime,sram,W/'sram-module',include_delay=PART=='delay' or os.environ.get('SM_SRAM_DELAY_FILTER')=='1',include_delay_filter=os.environ.get('SM_SRAM_DELAY_FILTER')=='1',full_delay=os.environ.get('SM_SRAM_FULL_DELAY')=='1',prefer_chord=PART=='chord' or os.environ.get('SM_SRAM_CHORD')=='1')
e.uc.mem_write(0x40000400,bytes(native));e.uc.mem_write(0x46700000,bytes(runtime));e.uc.mem_write(0x80000000,bytes(sram))
for patch in sr['patches']:e.uc.ctl_remove_cache(patch['at'],patch['at']+6)
e.uc.ctl_remove_cache(0x80000000,0x80010000)
module=next(x for x in sr['modules'] if x['name']==('low' if PART=='filter' else PART))
d=dict(code=module['at'],code_bytes=module['bytes'],symbols=module['symbols'],patches=[p for p in sr['patches'] if (0x40057000<=p['at']<0x40057200 if PART=='post' else p['at']>=0x46700000 and p['at']!=meta['fx_menu']['symbols']['fx_hall'])])
raw=W/'sram-tested.bin';raw.write_bytes(bytes(sram[d['code']-0x80000000:d['code']-0x80000000+d['code_bytes']]))
old_slow=e.emac._slow
for at in list(e.emac.fast):
 if 0x80005268<=at<0x800062b4:e.emac.fast.pop(at,None);e.emac.next.pop(at,None)
decoded=emac.disasm(str(raw),d['code'],d['code'],d['code']+d['code_bytes'])
actual={at for at,(size,mn,op) in decoded.items() if mn in ('macl','msacl','macw','msacw','movclrl') or (mn=='movel' and any(x in op for x in ['%acc','%macsr','%mask']))}
def guard(uc,at):
 if 0x80005268<=at<0x800062b4 and at not in actual:return
 return old_slow(uc,at)
e.emac._slow=guard;e.emac.install(decoded)
""".replace('PART',repr(part))
 if part=='post':
  start=source.index('native=bytearray(');end=source.index('buf=E.PARAMS',start);source=source[:start]+common+source[end:]
  source=source.replace("assert all(hit) and any(row['saved']>700 for row in rows),(hit,rows)", "assert all(hit),hit")
  source=source.replace('native post cases','SRAM post cases')
 elif part=='chord':
  start=source.index('native=bytearray(');end=source.index('regs=[',start)
  source=source[:start]+common+"\nsram=bytes(sram)\n"+source[end:]
  source=source.replace("meta['recovery_symbols']['chord_fast']","meta['chord_second']['symbols']['chord_fast']")
  source=source.replace("if kind.startswith('second') or kind.startswith('PM'):assert hits[1]>0 and cost[1]<cost[0]","if kind.startswith('second') or kind.startswith('PM'):assert hits[1]>0")
 elif part=='delay':
  start=source.index('native=bytearray(');end=source.index('regs=[',start)
  source=source[:start]+common+"\nCODE=d['code'];SITE=0x400576cc;old=meta['delay_static']['code']\n"+source[end:]
  source=source.replace("if kind!='ramp':assert cost[1]<cost[0]","assert cost[1]==cost[0],(kind,cost)")
 else:
  start=source.index('runtime=bytearray(');end=source.index('for label,lo,hi',start);source=source[:start]+common+source[end:]
  source=source.replace("assert cost[0]-cost[1] in (0,22),(name,case,cost)", "assert cost[1]>=cost[0],(name,case,cost)")
  source=source.replace("assert any(x['saved']==22 for x in rows)", "assert any(x['saved']<0 for x in rows)")
  source=source.replace('22 instructions saved per active lane','SRAM execution, unchanged samples/history')
exec(compile(source,__file__,'exec'))
