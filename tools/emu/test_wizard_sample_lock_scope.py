"""Un sample-lock ne protege que les parametres explicitement verrouilles.

Execute le wrapper courant, le stockage natif de locks et le refresh natif.
La delegation d'encodeur reste simulee comme dans la preuve de priorite.
"""
from pathlib import Path
source=Path(__file__).with_name('test_wizard_plock_priority.py').read_text().split('for slot in [10,11,12')[0]
exec(compile(source,__file__,'exec'))
alternate=0x420f0000;r.u.mem_write(alternate,bytes(100));r.u.mem_write(alternate+38,b'\x06')
cases=[]
for slot in (10,11,12,13,14,18,23,32):
    for explicit in (False,True):
        init_locks(slot);locked[0]=slot;step[0]=0
        r.w32(0x800017ec,alternate);r.u.mem_write(0x423087f8,bytes(48))
        if explicit:r.w32(0x423087f8+4*(slot>>5),1<<(slot&31))
        w16(frame+14+2*slot,8888);r.w32(0x800011e8+4*(7+slot),8888<<16)
        r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,4,1,0))
        assert r.call(s['aa_face_encoder'],0,EVENT)==77
        actual=r16(frame+14+2*slot);expected=8888 if explicit else 12345
        cases.append(dict(slot=slot,explicit_lock=explicit,actual=actual,expected=expected))
        assert actual==expected,('sample-lock overprotects an unlocked parameter',slot,explicit,actual,expected)
a.output.write_text(json.dumps(dict(cases=cases,hardware_tested=False),indent=2)+'\n')
print('PASS alternate sample sound: eight slots, explicit locks protected and unlocked controls retained',flush=True)
