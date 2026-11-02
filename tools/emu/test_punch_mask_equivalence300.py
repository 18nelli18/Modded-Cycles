"""Comparer le meme code PUNCH avant/apres le retrait des tests redondants.

Vrai payload, recettes et phases ; seul le delegate audio est simule afin
de comparer exactement le frame qu'il recoit et les etats a chaque bloc.
"""
from pathlib import Path
source=Path(__file__).with_name('test_control_all_undo.py').read_text().split("if m.get('cpu_monitor'):")[0].split('held=set();')[0]
exec(compile(source,__file__,'exec'))
import os,random
from unicorn import m68k_const as C
patch=json.loads(Path(os.environ['SM_MASK_PATCH']).read_text()) if os.environ.get('SM_MASK_PATCH') else m['punch_work_gate']
sy=m['activity_masks']['symbols'];ps=m['per_track_fx']['symbols'];frame=0x931a0000;observed=[]
bind(ps['mf_old_voice_playability'],lambda args:observed.append((args[:4],bytes(r.u.mem_read(args[1],476)))) or 0)
rng=random.Random(300287);machines=[0]*6;punch=[0]*6;cases=1000
registers=[getattr(C,'UC_M68K_REG_'+x) for x in ('D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6')]
for block in range(cases):
    if block%32==0:
        machines=[rng.randrange(29) for _ in range(6)];punch=[rng.choice((0,256,32512)) for _ in range(6)]
    if block%7==0:machines[rng.randrange(6)]=rng.randrange(29)
    if block%9==0:punch[rng.randrange(6)]=rng.choice((0,256,32512))
    data=bytearray(476)
    for track in range(6):
        for slot in range(33):struct.pack_into('>H',data,14+66*track+2*slot,rng.randrange(32513))
        struct.pack_into('>H',data,14+66*track+18,machines[track]<<8);struct.pack_into('>H',data,14+66*track+30,punch[track])
    trig=rng.randrange(64) if block%11==0 else 0;release=rng.randrange(64) if block%13==0 else 0
    initial_phase=bytes(r.u.mem_read(sy['phase'],72));initial_mask=r.r32(sy['pp_custom_mask']);results=[]
    for optimized in (False,True):
        for change in patch['patches']:r.u.mem_write(change['patch_site'],bytes.fromhex(change['patch_bytes'] if optimized else change['old_entry_bytes']))
        r.u.mem_write(sy['phase'],initial_phase);r.w32(sy['pp_custom_mask'],initial_mask);r.u.mem_write(frame,bytes(data))
        for i,reg in enumerate(registers):r.u.reg_write(reg,0x13570000+4*i)
        r.call(sy['pp_voice_loop'],0x931b0000,frame,trig,release)
        assert bytes(r.u.mem_read(frame,476))==bytes(data),('frame restoration',block,optimized)
        assert [r.u.reg_read(x) for x in registers]==[0x13570000+4*i for i in range(len(registers))],('ABI',block,optimized)
        results.append((observed[-1],bytes(r.u.mem_read(sy['phase'],72)),r.r32(sy['pp_custom_mask'])))
    assert results[0]==results[1],('PUNCH behavior changed',block,machines,punch)
a.output.write_text(json.dumps(dict(blocks=cases,tracks=6,native_delegate_frames_exact=True,private_phases_exact=True,selection_masks_exact=True,frame_restored=True,callee_saved_registers_exact=True,hardware_tested=False),indent=2)+'\n')
print('PASS 1000 randomized six-track PUNCH blocks: delegate frames, phases, masks, restored frame and ABI exact',flush=True)
