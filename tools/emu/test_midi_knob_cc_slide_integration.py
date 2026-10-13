#!/usr/bin/env python3
"""Slides CC placés : vrais fragments, queue bornée, Note Off prioritaire et UI."""
import argparse,json,pathlib,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
import build

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak',required=True);a=ap.parse_args()
    t=json.loads(pathlib.Path(a.tweak).read_text());s={k:int(v,16) for k,v in t['symbols'].items()}
    root=pathlib.Path(__file__).resolve().parents[2]
    catalog=json.loads((root/'work/midi-clear-catalog.json').read_text())
    tg=next(x for x in catalog['tweaks'] if x['id']=='model-tg-st')
    r=Rig(main_os_from_syx(a.cycles),tg,{'writes':[],'symbols':{}});r.s=s
    for w in t['writes']:r.u.mem_write(build.BASE+w['off'],bytes.fromhex(w['new']))
    for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
    pat,clock,runtime,worker,event=0x93070000,0x93076000,0x9307b000,0x93078000,0x93074000
    assert r.call('ml_init',pat)==1
    for name,value in (('ml_pattern',pat),('ml_play_pattern',pat),('ml_clock_state',clock),('ml_runtime',runtime),('mlp_track',0),('mlp_step',0),('ml_store_load_ready',1)):
        r.w32(s[name],value)
    r.w32(clock,1);r.w32(0x40fe4228,1);r.w32(s['TG_blk_clk'],100);r.w32(0x40149310,14400)
    r.u.mem_write(s['mlkc_state'],bytes((255,64))*72)
    r.u.mem_write(s['mlkc_state'],bytes((74,64,71,80)))
    r.u.mem_write(pat+8,bytes((72,100,1,1)));r.u.mem_write(pat+8+4*4,bytes((72,100,1,3)))
    locks=r.call('mlkc_locks_for',pat,1);assert locks
    for step,knob,cc,val in ((0,0,74,20),(4,0,74,100),(4,1,71,10)):
        assert r.call('mlkc_lock_set',locks,0,step,knob,cc,val)==1
    sent=[]
    def send(args):
        assert not r.u.reg_read(mk.UC_M68K_REG_SR)&0x700
        sent.append(bytes(r.u.mem_read(args[1],3)));return 0
    r.stubs[0x400826b0]=send;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2700)
    r.call('mlkcq_step',pat,0,0)
    state=s['mlkc_slide_states'];assert r.r32(state+8)==750 and r.r32(state+12)&0xfff==3
    assert not sent
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);r.call('mlkcq_worker')
    assert sent==[b'\xb6\x4a\x14']
    # Note Off réel du runtime avant le premier CC de rampe dans le worker.
    r.u.mem_write(runtime,bytes(320));r.w32(runtime,1);r.w32(runtime+8,1);r.w32(runtime+16,0x86480004)
    r.w32(worker+12,runtime);r.w32(s['mm_context'],0);r.w32(s['mlcc_context'],0)
    r.stubs[0x40001bb0]=lambda args:0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40001bb0,end=0x40001bb0)
    r.w32(s['TG_blk_clk'],300)
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2700)
    for _ in range(3):r.call('mlkc_slide_tick')
    assert len(sent)==1
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);r.call('ml_worker_once',worker)
    assert sent[1]==b'\x86\x48\x00' and sent[2][0]==0xb6
    for now in range(301,860):
        r.w32(s['TG_blk_clk'],now)
        r.u.reg_write(mk.UC_M68K_REG_SR,0x2700);r.call('mlkc_slide_tick')
        r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);r.call('mlkcq_worker')
    assert not (r.r32(state+12)&0xfff)
    up=[p[2] for p in sent if p[:2]==b'\xb6\x4a'];down=[p[2] for p in sent if p[:2]==b'\xb6\x47']
    assert up==sorted(up) and up[-1]==100 and len(set(up))>40
    assert down==sorted(down,reverse=True) and down[-1]==10 and len(set(down))>40
    assert all(p[0] in (0xb6,0x86) for p in sent)
    # Une réinitialisation pattern/Stop ne laisse aucune rampe ancienne active.
    r.call('mlkcq_step',pat,0,0);r.call('mlkcq_reset')
    assert all(r.r32(state+64*i+12)==0 for i in range(6))
    print('ok : fragments placés, armement q_step réel, deux rampes monotones, endpoint exact, Note Off natif avant CC, aucun port IRQ et reset')
    # Même raccourci et popup Model-TG sur la vraie page B, callbacks bruts.
    for name in ('ml_bank_ui_sync','mlp_keyboard','mlp_clip_key'):
        at=s[name];r.stubs[at]=lambda args,name=name:1 if name=='ml_bank_ui_sync' else 0
        r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    popups=[];at=s['TG_show_popup'];r.stubs[at]=lambda args:popups.append(r.string(args[0])) or 0
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    r.w32(s['TG_set_held'],0);r.w32(s['ml_genie_settings'],1)
    r.w32(s['mlp_func'],0);r.w32(s['mlp_held'],0);r.w32(s['mlp_remove'],0);r.w32(s['mlp_changed'],0)
    obj=0x9307f000;r.w32(s['mlp_obj'],obj)
    for original,want,text in ((1,3,'Slide on'),(3,1,'Slide off'),(2,3,'Slide on'),(0,3,'Slide on')):
        r.u.mem_write(pat+11,bytes((original,)));r.w32(event+12,16);r.w32(event+16,1)
        r.call('mlp_menu_key',obj,event)
        assert r.u.mem_read(pat+11,1)==bytes((want,)) and popups[-1]==text
        r.w32(event+16,0);r.call('mlp_menu_key',obj,event)
        assert r.u.mem_read(pat+11,1)==bytes((want,))
    print('ok : SETTINGS+TRIG brut, Slide on/off identiques, conversion trigless et release sans suppression')
    # Réutiliser la vraie phase du Model-TG lié, pas une phase inventée.
    ledstates=[];claims=0x9307f600
    for at,fn in ((0x400cfaf4,lambda args:0x9307f700),(0x4000608c,lambda args:args[0]+1),(0x400060bc,lambda args:args[0]+20),(0x40005f86,lambda args:ledstates.append((args[1],args[2])) or 0)):
        r.stubs[at]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    at=s['mlp_cursor'];r.stubs[at]=lambda args:0xffffffff
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    for phase,expected in ((0,1),(79,1),(80,3),(159,3),(160,1),(239,1),(240,3),(1023,3),(1024,1)):
        r.w32(s['TG_blk_clk'],phase);ledstates.clear()
        r.call('mlp_led',obj+0x500,0,claims)
        assert (1,expected) in ledstates,(phase,ledstates)
    print('ok : double-blink B utilise la vraie phase Model-TG, neuf limites de phase vérifiées')

    # Détecter le raccordement audio réel sans simuler des cycles d'OS entiers.
    hook=struct.pack('>HI',0x4eb9,s['mlkc_slide_tick'])
    start=s['ml_audio_tick'];end=s['ml_ui_drain']
    assert hook in bytes(r.u.mem_read(start,end-start))
    print('ok : appel slide_tick présent dans adaptateur audio avant réveil worker')
    print('Expérimental : vérifier sur matériel, avec CC externes et routage DIN/USB.')

if __name__=='__main__':main()
