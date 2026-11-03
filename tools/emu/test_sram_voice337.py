"""Tables ST deplacees : voix stock/ajoutees et post/filtres/HALL identiques.

Restaurer toutes les banques RAM et le contexte EMAC entre les deux lectures
du meme scenario. Toute lecture des anciennes tables depuis un autre noyau
que les nouveaux occupants SRAM est une erreur, meme si le PCM semble juste.
"""
from pathlib import Path
setup=Path(__file__).with_name('test_rebuild300_cold_audio.py').read_text().split('events=[]')[0]
exec(compile(setup,__file__,'exec'))
import copy
# Supprimer les anciens decodages qui appartenaient aux banques de staging.
for at in list(e.emac.fast):
 if 0x80000000<=at<0x80010000:e.emac.fast.pop(at,None);e.emac.next.pop(at,None)
current_sram=emac.disasm(str(W/'final-sram.bin'),0x80000000,0x80001c5c,0x800074b4)
e.emac.install(current_sram)
valid_sram={at for at,(size,mn,op) in current_sram.items() if mn in ('macl','msacl','macw','msacw','movclrl') or (mn=='movel' and any(x in op for x in ['%acc','%macsr','%mask']))}
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from sram_audio337 import apply,SRAM,SRAM_END,DDR,DDR_END
include_delay=os.environ.get('SM_SRAM_DELAY')=='1'
if include_delay:
 e.uc.mem_map(0xfc040000,0x10000);e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(0x40057260);e.call(0x4005770e)
native=bytearray(e.uc.mem_read(0x40000400,0x1ffc00));runtime=bytearray(e.uc.mem_read(0x46700000,0x300000));sram=bytearray(e.uc.mem_read(0x80000000,65536))
old_sram=bytes(sram);d=apply(meta,native,runtime,sram,W/'sram-module',include_delay=include_delay,include_delay_filter=os.environ.get('SM_SRAM_DELAY_FILTER')=='1',full_delay=os.environ.get('SM_SRAM_FULL_DELAY')=='1',prefer_chord=os.environ.get('SM_SRAM_CHORD')=='1');enabled=[False];reads=[0];hits={row['name']:0 for row in d['modules']}
actual=set();old_slow=e.emac._slow
for at in list(e.emac.fast):
 if SRAM<=at<SRAM_END:e.emac.fast.pop(at,None);e.emac.next.pop(at,None)
for row in d['modules']:
 if row['name']=='hall':continue
 raw=W/('actual-'+row['name']+'.bin');raw.write_bytes(bytes(sram[row['at']-0x80000000:row['at']-0x80000000+row['bytes']]))
 decoded=emac.disasm(str(raw),row['at'],row['at'],row['at']+row['bytes'])
 actual.update(at for at,(size,mn,op) in decoded.items() if mn in ('macl','msacl','macw','msacw','movclrl') or (mn=='movel' and any(x in op for x in ['%acc','%macsr','%mask'])))
 e.emac.install(decoded)
def guard(uc,at):
 if SRAM<=at<SRAM_END:
  if not enabled[0] or at not in actual:return
 elif 0x80000000<=at<0x80010000 and at not in valid_sram:return
 return old_slow(uc,at)
e.emac._slow=guard
def forbid(uc,access,at,size,value,data):
 if enabled[0]:
  pc=uc.reg_read(C.UC_M68K_REG_PC)
  assert SRAM<=pc<SRAM_END,('old SRAM table read',hex(at),hex(pc))
  reads[0]+=1
e.uc.hook_add(UC_HOOK_MEM_READ,forbid,begin=SRAM,end=SRAM_END-1)
for row in d['modules']:
 e.uc.hook_add(UC_HOOK_CODE,lambda *args,name=row['name']:hits.__setitem__(name,hits[name]+int(enabled[0])),begin=row['at'],end=row['at'])
def install(on):
 enabled[0]=on
 if not on:
  e.uc.mem_write(SRAM,old_sram[SRAM-0x80000000:SRAM_END-0x80000000])
  for patch in d['operand_patches']:e.uc.mem_write(patch['at'],struct.pack('>I',patch['old']))
  for patch in d['patches']:
   e.uc.mem_write(patch['at'],bytes.fromhex(patch['old']));e.uc.ctl_remove_cache(patch['at'],patch['at']+6)
  e.uc.ctl_remove_cache(0x80000000,0x80010000)
  return
 e.uc.mem_write(DDR,bytes(runtime[DDR-0x46700000:DDR_END-0x46700000]));e.uc.mem_write(SRAM,bytes(sram[SRAM-0x80000000:SRAM_END-0x80000000]))
 for patch in d['operand_patches']:
  e.uc.mem_write(patch['at'],struct.pack('>I',patch['new']))
 for patch in d['patches']:
  e.uc.mem_write(patch['at'],bytes.fromhex(patch['new']));e.uc.ctl_remove_cache(patch['at'],patch['at']+6)
 e.uc.ctl_remove_cache(0x80000000,0x80010000)
def invalid(uc,access,at,size,value,data):
 print('UNMAPPED',hex(at),'PC',hex(uc.reg_read(C.UC_M68K_REG_PC)),'SRAM',enabled[0],flush=True)
 return False
e.uc.hook_add(UC_HOOK_MEM_INVALID,invalid)
rows=[]
# Garder la pile aussi : aucun historique natif non initialise ne doit venir
# artificiellement du passage precedent dans l autre variante.
regions=[(a,b-a+1) for a,b,permission in e.uc.mem_regions() if a<0xfc000000]
for label,machines in [('stock',[0,1,2,3,4,5]),('added',[7,8,9,10,11,0])]:
 install(False)
 for t,machine in enumerate(machines):
  e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE)
  e.set(t,machine=machine,note=48+t*3,color=64,shape=64,sweep=64,contour=64,decay=110,punch=1,gate=0)
 saved=[bytes(e.uc.mem_read(at,size)) for at,size in regions];context=e.uc.context_save();mode=e.emac.macsr;acc=[e.emac.physical(i) for i in range(4)];tracks=copy.deepcopy(e.trk);outputs=[]
 for on in [False,True]:
  enabled[0]=False
  for (at,size),raw in zip(regions,saved):e.uc.mem_write(at,raw)
  e.uc.context_restore(context);e.emac.macsr=mode
  for i,value in enumerate(acc):e.emac.put_physical(i,value)
  e.trk=copy.deepcopy(tracks);e.uc.ctl_remove_cache(0x80000000,0x80010000)
  for patch in d['patches']:e.uc.ctl_remove_cache(patch['at'],patch['at']+6)
  install(on);blocks=[]
  for block in range(12):
   for t in range(6):e.set(t,color=[0,64,127][block//4],shape=[0,64,127][block//4])
   e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);voice=e.block(63 if block in (0,4,8) else 0)
   e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(0x40056f58,E.TRACK_BASE,E.PARAMS)
   for t in range(6):
    e.uc.mem_write(0x401bbd60+4*t,struct.pack('>I',127+block*250));e.uc.mem_write(0x401bbd7c+4*t,struct.pack('>I',block*1200))
    e.call(meta['recovery_symbols']['pf_run'],E.TRACK_BASE+128*t,t)
   data=bytes(e.uc.mem_read(E.TRACK_BASE,768));wet=E.PARAMS+0x1a000;params=wet+512;e.uc.mem_write(params,struct.pack('>2h',64*256,32*256))
   e.call(meta['fx_menu']['symbols']['fx_hall'],wet,E.TRACK_BASE,params)
   delay_output=b''
   if include_delay:
    e.call(meta['per_track_fx']['symbols']['mf_old_native_delay'],wet+0x1000,E.TRACK_BASE,params);delay_output=bytes(e.uc.mem_read(wet+0x1000,256))
   blocks.append((voice.copy(),data,bytes(e.uc.mem_read(wet,256)),delay_output))
  outputs.append(blocks)
 for block,(x,y) in enumerate(zip(*outputs)):
  assert np.array_equal(x[0],y[0]) and x[1:]==y[1:],(label,block)
 rows.append(dict(case=label,blocks=12,voice_post_filter_HALL_exact=True));print('PASS SRAM tables and full audio chain',label,flush=True)
assert all(value for name,value in hits.items() if name!='delay_feedback_a'),hits
args.output.write_text(json.dumps(dict(cases=rows,SRAM_execution_hits=hits,old_table_reads_forbidden=True,HALL_rodata_reads=reads[0],module=d,hardware_tested=False),indent=2)+'\n');print('PASS relocated tables, actual SRAM execution and complete stock/added audio cases',hits)
