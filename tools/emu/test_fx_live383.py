"""FX pendant lecture : vrai raccord Song, ordres audio/UI alternes et sauvegarde."""
from pathlib import Path

source=Path(__file__).with_name('test_fx_mst_save379.py').read_text()
exec(compile(source,__file__,'exec'))

live_entry=m['acid_articulation']['symbols']['sg_live_switch']
chain=0x9301c000
r.w32(0x40a7883c,1)
def live(id,audio_first):
    r.w32(chain,RAW+28+id*STRIDE)
    keep=[getattr(C,'UC_M68K_REG_'+name) for name in ('D0','D1','D2','D3','D4','D5','D6','D7','A0','A2','A3','A4','A5','A6')]
    for n,reg in enumerate(keep):r.u.reg_write(reg,0x12340000+n)
    r.u.reg_write(C.UC_M68K_REG_A1,chain)
    r.u.reg_write(C.UC_M68K_REG_SR,0x201f)
    call(live_entry)
    assert all(r.u.reg_read(reg)==0x12340000+n for n,reg in enumerate(keep))
    assert r.u.reg_read(C.UC_M68K_REG_A1)==chain
    # Unicorn garde certains CCR paresseux : les lire par MOVE SR reel.
    probe=0x9301d000;r.u.mem_write(probe,bytes.fromhex('40c04e75'))
    actual_sr=call(probe)&0xffff
    assert actual_sr==0x2010,hex(actual_sr)
    if audio_first:
        call('mf_sync_audio');call('fxs_ui')
    else:
        call('fxs_ui');call('mf_sync_audio')
    expected=1 if id==0 else 0
    assert r.r32(s['ch_mode'])==expected, ('FX live',id,audio_first,r.r32(s['ch_mode']),expected)
    assert r.r32(s['cr_mode'])==(11 if id==0 else 0)
# La demande native est differee : aucun FX ne change avant la frontiere.
r.w32(chain,RAW+28);r.w32(chain+4,RAW+0x2cfc5c)
r.w32(0x40a78920,0)
before=r.r32(s['ch_mode']),r.r32(s['cr_mode'])
call(0x40055cd6,chain,1);call('fxs_ui')
assert (r.r32(s['ch_mode']),r.r32(s['cr_mode']))==before
for audio_first in (True,False):
    for id in (0,1,0,1,1,0,1,0):live(id,audio_first)
print('PASS transitions live A/B, deux ordres audio/UI, retour inverse et meme pattern',flush=True)
r.w32(0x40a7883c,0)
assert call(0x4000f762,HOLDER,9,CB)&255
blob=projects[9];disk=dict(files)
r,s,files,projects=fixture(disk)
r.u.mem_write(CB,bytes(16));call(0x40061738,RAW);r.u.mem_write(SER,blob)
assert call(0x4006a5a0,0x93018000,9,RAW,CB)&255
activate(0);call('mf_frame');r.w32(0x40a7883c,1)
for id in (1,0,1,0):live(id,True)
a.output.write_text(json.dumps(dict(sha256=m['sha256'],live_cases=20,queued_request_deferred=True,general_registers_preserved=True,SR_IPL_CCR_preserved=True,save_reload_after_live=True,hardware_tested=False),indent=2)+'\n')
print('PASS sauvegarde/relecture apres transitions live ; aucun resultat appareil',flush=True)
