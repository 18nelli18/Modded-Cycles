"""Masques du vrai payload : changements de banque/machine et retour au stock.

Les delegates de synthese/LFO sont simules pour isoler le dispatch des masques.
Les preuves PCM et d'etats natifs restent distinctes de cette preuve de gating.
"""
from pathlib import Path
source=Path(__file__).with_name('test_control_all_undo.py').read_text().split("if m.get('cpu_monitor'):")[0].split('held=set();')[0]
exec(compile(source,__file__,'exec'))
import os,hashlib
from unicorn import UC_HOOK_CODE
sy=m['activity_masks']['symbols'];ps=m['per_track_fx']['symbols'];u=r.u
if os.environ.get('SM_MASK_PATCH'):
    patch=json.loads(Path(os.environ['SM_MASK_PATCH']).read_text())
    for change in patch['patches']:
        assert bytes(u.mem_read(change['patch_site'],len(bytes.fromhex(change['old_entry_bytes']))))==bytes.fromhex(change['old_entry_bytes'])
        u.mem_write(change['patch_site'],bytes.fromhex(change['patch_bytes']))
frame,second,third,fourth=0x931a0000,0x93190000,0x93191000,0x93192000
primary=[];updates=[];observed=[];counter=[0]
bind(0x40091ab2,lambda args:primary.append(args) or 0)
bind(ps['li_sync_fast'],lambda args:0)
bind(ps['li_update'],lambda args:updates.append(args) or 0)
bind(ps['mf_old_voice_playability'],lambda args:observed.append(bytes(u.mem_read(args[1],476))) or 0)
u.hook_add(UC_HOOK_CODE,lambda *args:counter.__setitem__(0,counter[0]+1))
for context in (second,third,fourth):
    u.mem_write(context,bytes(2048))
    for track in range(6):u.mem_write(context+192+16*track+6,struct.pack('>H',127<<8))
r.w32(ps['li_context'],second);r.w32(ps['li_extra'],third);r.w32(ps['li_extra']+4,fourth)
u.mem_write(frame,bytes(476))
cases=[]
def lfo(count,context,expected,expected_updates):
    primary.clear();updates.clear();r.w32(ps['li_count'],count);r.w32(ps['li_context'],context)
    u.mem_write(sy['li_active_tracks'],b'\xff'*12);r.w32(ps['li_noapply'],0)
    r.call(sy['li_dispatch'],frame,30000,0)
    actual=list(struct.unpack('>3I',u.mem_read(sy['li_active_tracks'],12)))
    assert actual==expected,(count,context,actual,expected)
    assert len(primary)==1 and len(updates)==expected_updates
    assert r.r32(ps['li_noapply'])==0
    cases.append(dict(count=count,context=context,masks=actual,secondary_updates=len(updates)))
lfo(1,second,[0,0,0],0);lfo(4,second,[0,0,0],0)
for context,track,destination in ((second,0,11),(third,3,24),(fourth,5,32)):
    u.mem_write(context+192+16*track+6,struct.pack('>H',destination<<8))
lfo(4,second,[1,8,32],3);lfo(2,second,[1,0,0],1);lfo(4,0,[0,0,0],0)
u.mem_write(second+192+6,struct.pack('>H',127<<8))
lfo(2,second,[0,0,0],0)
for context in (third,fourth):
    for track in range(6):u.mem_write(context+192+16*track+6,struct.pack('>H',127<<8))
lfo(4,second,[0,0,0],0)
def punch(machine,on,trigger):
    data=bytearray(476)
    for track in range(6):
        for slot in range(33):struct.pack_into('>H',data,14+66*track+2*slot,64<<8)
        struct.pack_into('>H',data,14+66*track+18,machine<<8);struct.pack_into('>H',data,14+66*track+30,256 if on else 0)
    u.mem_write(frame,bytes(data));counter[0]=0;r.call(sy['pp_voice_loop'],0x931b0000,frame,trigger,0)
    assert bytes(u.mem_read(frame,476))==bytes(data),'PUNCH did not restore the private frame'
    return bytes(data),counter[0]
for machine in range(25):
    for on in (False,True):
        original,_=punch(machine,on,63)
        expected=63 if on and machine>=6 and machine not in (13,17,21) else 0
        assert r.r32(sy['pp_custom_mask'])==expected,(machine,on)
        if machine<6 or not on and machine!=21:assert observed[-1]==original
_,first=punch(20,True,63)
for _ in range(181):original,expired=punch(20,True,0)
assert observed[-1]==original and r.r32(sy['pp_custom_mask'])==63
original,stock=punch(0,True,0);assert observed[-1]==original and r.r32(sy['pp_custom_mask'])==0
a.output.write_text(json.dumps(dict(lfo_cases=cases,punch_cases=50,stock_punch_unchanged=True,stale_lfo_bits_recomputed=True,custom_to_stock_clears_punch_mask=True,expired_transient_keeps_punch_selection_mask=True,dispatch_instructions=dict(first=first,expired=expired,stock=stock),delegates_stubbed=True,hardware_tested=False),indent=2)+'\n')
print('PASS live mask transitions: factory LFO always delegated, secondary bits recomputed, custom-to-stock PUNCH clean; instructions',first,expired,stock,flush=True)
