"""SIL : garde de commit reentrant, dans la queue libre du helper de reveil309."""
import hashlib,struct

def apply(meta,native,runtime,sram,out):
    base=0x46700000;owner=meta['fx_energy'];code=owner['code']+owner['reclaimed_bytes']-64
    code=(code+3)&~3
    assert code>=owner['code']+owner['code_bytes']
    assert not any(runtime[code-base:code-base+48])
    sy=meta['activity_masks']['symbols'];precise=meta['filter_pattern300']['symbols']
    at=sy['mb_display_machine'];committing=precise['committing'];pending=sy['mb_pending']
    if at!=precise['mb_display_machine']:
        # Optional a regenere le navigateur ; verifier le delegue et le verrou reel.
        entry=precise['mb_display_machine']-base
        assert runtime[entry:entry+6]==bytes.fromhex('4ef9')+struct.pack('>I',at)
        committing=pending+24
        key=sy['mb_key']-base;body=bytes(runtime[key:at-base])
        assert bytes.fromhex('23c0')+struct.pack('>I',committing) in body
        assert bytes.fromhex('42b9')+struct.pack('>I',committing) in body
    old=bytes(runtime[at-base:at-base+6])
    assert old==bytes.fromhex('2039')+struct.pack('>I',pending)
    # tst.l committing ; beq original ; move.l 4(sp),d0 ; rts ; original ; jmp suite
    blob=bytes.fromhex('4ab9')+struct.pack('>I',committing)+bytes.fromhex('6706202f00044e75')+old+bytes.fromhex('4ef9')+struct.pack('>I',at+6)
    assert len(blob)<=48 and code+len(blob)<=owner['code']+owner['reclaimed_bytes']
    new=bytes.fromhex('4ef9')+struct.pack('>I',code)
    runtime[code-base:code-base+len(blob)]=blob;runtime[at-base:at-base+6]=new
    return dict(code=code,code_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),committing=committing,patches=[dict(at=at,old=old.hex(),new=new.hex())],new_state_bytes=0,audio_hooks_changed=False,hardware_tested=False)
