"""Sample-lock : vraie copie du son et vrais locks, entre plusieurs notes.

Le token de sample reste celui du pool ; ses parametres non verrouilles
doivent suivre le son de piste. Aucun decodeur audio ni E/S simule dans ces appels.
"""
from pathlib import Path
source=Path(__file__).with_name('test_wizard_plock_priority.py').read_text().split('for slot in [10,11,12')[0]
exec(compile(source,__file__,'exec'))
alternate=0x420f0000;alternate2=alternate+128;descriptor=alternate+512
for ptr,name in ((alternate,b'SMP1234ABCD'),(alternate2,b'SMP5678ABCD')):
    r.u.mem_write(ptr,bytes(100));r.u.mem_write(ptr+4,name+b'\0');r.u.mem_write(ptr+38,b'\x06')
    for slot in range(33):w16(ptr+20+2*slot,8888)
    r.u.mem_write(ptr+38,b'\x06')
original=[bytes(r.u.mem_read(ptr,100)) for ptr in (alternate,alternate2)]
for slot in range(33):w16(sound(0)+20+2*slot,12345)
r.u.mem_write(sound(0)+38,b'\x06')
cases=[]
for slot in (10,11,12,13,14,18,23,32):
    r.call(0x40058a0a,alternate,0)
    actual=r16(frame+14+2*slot)
    assert actual==12345,('sample-lock snapshots an unlocked parameter',slot,actual)
    assert r.r32(0x800017ec)==alternate,'sample identity lost'
    r.u.mem_write(descriptor,bytes(28));r.w32(descriptor+8,1)
    w16(descriptor+20,slot);w16(descriptor+22,7777)
    r.call(0x400583da,0,descriptor,frame)
    assert r16(frame+14+2*slot)==7777,'explicit lock lost'
    w16(sound(0)+20+2*slot,23456)
    r.call(0x40058308,0,frame,alternate)
    assert r16(frame+14+2*slot)==23456,'restore uses stale sample preset'
    r.call(0x40058a0a,alternate2,0)
    assert r16(frame+14+2*slot)==23456,'next sample trigger loses knob edit'
    assert r.r32(0x800017ec)==alternate2
    r.call(0x400583da,0,descriptor,frame)
    assert r16(frame+14+2*slot)==7777
    assert original==[bytes(r.u.mem_read(ptr,100)) for ptr in (alternate,alternate2)],'stored pool sounds mutated'
    w16(sound(0)+20+2*slot,12345);cases.append(slot)
# Un vrai preset, ou une autre machine de base, garde les valeurs du preset.
r.u.mem_write(alternate+4,b'CUSTOM PRESET\0');r.call(0x40058a0a,alternate,0)
assert r16(frame+14+20)==8888
r.u.mem_write(alternate+4,b'SMP1234ABCD\0');r.u.mem_write(sound(0)+38,b'\x04');r.call(0x40058a0a,alternate,0)
assert r16(frame+14+20)==8888
# Comparaison native avant/apres pour les six machines stock, y compris
# l'etat de lissage et tous les registres sauvegardes par l'ABI.
hooks=m['wizard_sample_inherit']['hooks'];saved=[bytes(r.u.mem_read(x['address'],8)) for x in hooks]
preserved=[getattr(C,'UC_M68K_REG_'+x) for x in ('D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6')]
for machine in range(6):
    r.u.mem_write(alternate+38,bytes([machine]));outputs=[]
    for patched in (False,True):
        for hook,new in zip(hooks,saved):r.u.mem_write(hook['address'],new if patched else bytes.fromhex(hook['old']))
        r.u.mem_write(frame,bytes(480));r.u.mem_write(0x800011e8,bytes(1024))
        for i,reg in enumerate(preserved):r.u.reg_write(reg,0x13570000+4*i)
        r.call(0x40058a0a,alternate,0)
        registers=[r.u.reg_read(x) for x in preserved]
        assert registers==[0x13570000+4*i for i in range(len(preserved))],('ABI',machine,patched,registers)
        outputs.append((bytes(r.u.mem_read(frame,480)),bytes(r.u.mem_read(0x800011e8,1024))))
    assert outputs[0]==outputs[1],('stock sound copy changed',machine)
a.output.write_text(json.dumps(dict(slots=cases,native_sound_copy=True,native_lock_application=True,sample_identity_preserved=True,pool_unchanged=True,ordinary_edits_survive_following_sample=True,other_presets_unchanged=True,six_stock_copies_exact=True,callee_saved_registers_preserved=True,hardware_tested=False),indent=2)+'\n')
print('PASS native sample sound copy/restore, explicit locks, later knob edits and alternating samples; other presets unchanged',flush=True)
