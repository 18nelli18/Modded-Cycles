#!/usr/bin/env python3
"""Banque actuelle : vrai SYX navigateur, bootstrap, absence de service precoce,
clavier B et scheduler. I/O physiques simulees ; pas de resultat materiel.
"""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,STACK,STOP,RAW,EVENT,OBJ,VT,GET,SIGNAL
from test_sdvintage import main_os_from_syx
import build

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',required=True);p.add_argument('--scheduler',action='store_true');a=p.parse_args()
    prefix=pathlib.Path(a.case);cat=json.loads(prefix.with_suffix('.json').read_text())['tweaks']
    bank=next(t for t in cat if t['id']=='midi-out-bank');img=main_os_from_syx(str(prefix.with_suffix('.syx')))
    r=Rig(img,{'writes':[]},{'writes':[],'symbols':bank['symbols']});u=r.u
    for at,size in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:u.mem_map(at,size)
    u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
    def fault(u,access,addr,size,value,data):print('FAULT',hex(u.reg_read(mk.UC_M68K_REG_PC)),hex(addr),size,flush=True);return False
    u.hook_add(UC_HOOK_MEM_INVALID,fault)
    def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
    sites=set()
    for at,raw in [(build.BASE,img)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for p in bank['append']['parts'] if 'hex' in p]:
        sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
    for site in sites:u.hook_add(UC_HOOK_CODE,cache,begin=site,end=site)
    u.emu_start(0x40000530,0x4000053a,count=200_000_000)
    assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a,'boot incomplet'
    assert r.r32(r.s['ml_context'])==0,'allocation B avant ouverture'
    print('ok vrai bootstrap/clear ; aucune allocation B avant ouverture',flush=True)
    expected=[]
    for part in bank['append']['parts']:
        if 'hex' not in part:continue
        at=int(part['dest'],16);raw=bytes.fromhex(part['hex'])
        if at<=r.s['ml_context']<at+len(raw):expected.append((at,raw))
    assert len(expected)==1
    if 'mp_api' in r.s:
        # L'extension de persistance doit aussi survivre au vrai chargeur et
        # au constructeur cache ; ne pas la recharger artificiellement ici.
        for part in bank['append']['parts']:
            if 'hex' not in part:continue
            at=int(part['dest'],16);raw=bytes.fromhex(part['hex'])
            if at<=r.s['mp_api']<at+len(raw):expected.append((at,raw))
        assert len(expected)==2,'extension persistance absente'
    for at,raw in expected:assert bytes(u.mem_read(at,len(raw)))==raw,'code Banque modifie au boot'
    r.call(0x4007929c)
    for at,raw in expected:assert bytes(u.mem_read(at,len(raw)))==raw,'cache disque ecrase Banque'
    print('ok code Banque exact, cache disque natif intact',flush=True)
    # Les premiers callbacks LED/UI sont invoques avec singletons absents.
    for ui,router in [(0,0),(1,0),(0,1)]:
        r.w32(0x40fe4178,ui);r.w32(0x40fe4228,router)
        for addr in (0x400ff9b8,0x400ffa78,0x40103070,0x401031b4,0x40107e18):r.call(r.r32(addr))
        r.call('midi_current_safe_ui');assert r.r32(r.s['ml_context'])==0
    print('ok callbacks precoces : aucune allocation ni sortie avec UI/MIDI absents',flush=True)
    # Meme fixture que les preuves historiques : seul le materiel et les objets
    # UI exterieurs sont simules ; prepare, hooks, clavier et files sont reels.
    r.w32(0x40fe4178,0x93005000);r.w32(OBJ,VT);r.w32(VT+40,GET);r.w32(VT+16,SIGNAL)
    u.mem_write(GET,b'\x20\x3c'+struct.pack('>I',RAW)+b'\x4e\x75')
    r.w32(0x93005030,0x93005100);r.w32(0x93005128,0x93005200)
    u.mem_write(0x93005200,b'\x20\x3c'+struct.pack('>I',0x93005300)+b'\x4e\x75');r.w32(0x93005304,0)
    u.mem_write(RAW,bytes(722));u.mem_write(RAW+713,struct.pack('>H',16));saved=bytes(u.mem_read(RAW,722))
    r.w32(r.s['TG_set_held'],1);r.event(2,3,1)
    assert r.call(0x4007240c,EVENT)==0
    obj=r.r32(r.s['mlp_obj']);ctx=r.r32(r.s['ml_context']);assert obj and ctx
    r.event(2,2,2);assert r.call(0x4007240c,EVENT)==0
    assert bytes(u.mem_read(RAW,722))==saved
    print('ok entree B par FUNC+SETTINGS+TRACK ; donnees A inchangees',flush=True)
    state=0x930a0000
    for addr,fn in ((0x400cf9a8,lambda a:state),(0x4000f208,lambda a:0x930a1000),(0x4000cfcc,lambda a:0x930a2000),(0x40016da6,lambda a:8)):
        r.stubs[addr]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.w32(r.s['TG_set_held'],0)
    live=r.s['ml_live_runtime'];pattern=r.r32(r.s['ml_pattern'])
    for lane in range(6):u.mem_write(pattern+264*lane+6,b'\x08')
    for lane in range(6):
        r.w32(r.s['mlp_track'],lane)
        for key in range(16):
            r.event(16+key,1,3+key*2);r.call('mlp_menu_key',obj,EVENT)
            assert r.call('ml_take',live)==((0x96+lane)<<24)|((60+key)<<16)|(100<<8)|4
            r.event(16+key,0,4+key*2);r.call('mlp_menu_key',obj,EVENT)
            assert r.call('ml_take',live)==((0x86+lane)<<24)|((60+key)<<16)|4
    assert bytes(u.mem_read(RAW,722))==saved
    print('ok clavier B : 96 notes et releases sur canaux 7-12 ; A intact',flush=True)
    # Verifier les fonctions relogees, et non une compilation de test separee.
    locks,copy=0x93060000,0x93064000
    assert r.call('mlkc_lock_init',locks)==1 and r.call('mlkc_lock_init',copy)==1
    for lane in range(6):
        for step in (0,15,16,63):
            for knob in range(12):
                value=(lane+step+knob)%128
                assert r.call('mlkc_lock_set',locks,lane,step,knob,74,value)==1
                assert r.call('mlkc_lock_get',locks,lane,step,knob)==(74<<8)|value
    assert r.call('mlkc_lock_set',locks,0,1,0,0,0)==1
    assert r.call('mlkc_lock_get',locks,0,1,0)==0
    assert r.call('mlkc_lock_copy',copy,5,63,locks,0,16)==1
    for knob in range(12):assert r.call('mlkc_lock_get',copy,5,63,knob)==(74<<8)|((16+knob)%128)
    assert r.call('mlkc_lock_clear',copy,5,63)==1
    assert bytes(u.mem_read(copy,9216))==b'\xff'*9216
    for start,target in ((0,127),(127,0),(64,64),(1,126),(126,1)):
        for duration in (1,7,127,32768,65535,200000):
            times=sorted({0,duration//4,duration//2,3*duration//4,duration,duration+1})
            values=[r.call('mlkc_slide_value',start,target,t,duration) for t in times]
            assert values[0]==start and values[-1]==target
            assert all(min(start,target)<=v<=max(start,target) for v in values)
            assert values==sorted(values,reverse=target<start)
    print('ok locks CC : six voies, 64 pas, 12 potards, copie/clear ; slides montants/descendants',flush=True)
    if 'SG_config' in r.s:
        cfg=r.s['SG_config'];adv=r.s['SG_advanced'];opts=r.s['SG_options']
        for off,val in [(4,100),(8,48),(12,72),(24,123456)]:r.w32(cfg+off,val)
        for off,val in [(0,80),(4,110),(24,0),(28,100),(32,0),(36,4),(40,0)]:r.w32(adv+off,val)
        for off in [0,4,8]:r.w32(opts+off,0)
        r.w32(0x40a7883c,0);r.call('ml_repeat_prepare_ui')
        for lane in range(6):
            r.w32(r.s['mlp_track'],lane);before=bytes(u.mem_read(pattern,1584))
            r.call('ml_genie_generate');assert r.r32(r.s['SG_error'])==0
            got=bytes(u.mem_read(pattern,1584));lo=264*lane
            assert before[:lo]==got[:lo] and before[lo+264:]==got[lo+264:]
            assert all(got[lo+8+4*i+3]&1 and got[lo+8+4*i+1]>0 for i in range(16))
            assert bytes(u.mem_read(RAW,722))==saved
            r.call('ml_genie_undo');assert bytes(u.mem_read(pattern,1584))==before
        print('ok Genie : six voies B isolees, velocites audibles et Undo exact ; A intact',flush=True)
    # TEMPO ne doit pas etre absorbe par le clavier B, appui ou relachement.
    assert r.call('mlp_menu_key',obj,r.event(14,1))==0
    assert r.call('mlp_menu_key',obj,r.event(14,0))==0
    print('ok TEMPO : appui et relachement transmis au menu natif',flush=True)
    r.call('mlp_dtor1',obj)
    if a.scheduler:
        from test_midi_lane_scheduler import prove
        prove(r)

if __name__=='__main__':main()
