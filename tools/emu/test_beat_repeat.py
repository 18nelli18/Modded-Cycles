"""Note 99 : vrais corps ColdFire, gestes maintenus et six historiques audio.

python3 tools/emu/test_beat_repeat.py --cycles firmware/model-cycles_OS1.13.syx
 --data build/beat-repeat-data.json
Allocation et sortie gain simulees ; aucun resultat materiel invente.
"""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP,EVENT
from test_sdvintage import main_os_from_syx
ORIGIN=0x46a00000
N=131072
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',default='firmware/model-cycles_OS1.13.syx');p.add_argument('--data',required=True);p.add_argument('--case');p.add_argument('--meter',action='store_true');a=p.parse_args()
    data=json.loads(pathlib.Path(a.data).read_text());stock=main_os_from_syx(a.cycles)
    case=None;origin=ORIGIN
    if a.case:
        prefix=pathlib.Path(a.case);case=json.loads(prefix.with_suffix('.json').read_text())
        tweak=next(t for t in case['tweaks'] if t['id']=='control-all-beat-repeat')
        stock=main_os_from_syx(str(prefix.with_suffix('.syx')));origin=int(tweak['append']['dest'],16)
    r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
    u.mem_map(0x43000000,0x800000);u.mem_map(0x46700000,0x400000);u.mem_map(0x80000000,0x200000);u.mem_map(0x93200000,0x400000)
    code=bytearray.fromhex(data['hex'])
    for off in data['reloc']:struct.pack_into('>I',code,off,struct.unpack_from('>I',code,off)[0]+origin)
    r.s={k:origin+v for k,v in data['symbols'].items()}
    if case:
        expected=bytes.fromhex(tweak['append']['parts'][0]['hex'])
        for name in ('br_old_key','br_old_gain','br_side','br_side_on','br_mask_address','br_old_track_keys','br_old_track_leds','br_load_address','br_avg_address','br_fading_address','br_stolen_address','br_filter_f_address','br_filter_q_address','br_filter_mk_address','br_filter_modes_address'):
            if name not in data['symbols']:continue
            off=data['symbols'][name];code[off:off+4]=expected[off:off+4]
        assert bytes(code)==expected,'module navigateur different du module prouve'
        def cache(uc,pc,size,user):uc.reg_write(mk.UC_M68K_REG_PC,pc+4)
        sites=set()
        for at,raw in [(0x40000400,stock)]+[(int(part['dest'],16),bytes.fromhex(part['hex'])) for t in case['tweaks'] if 'append' in t for part in t['append']['parts'] if 'hex' in part]:
            sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
        for at in sites:u.hook_add(UC_HOOK_CODE,cache,begin=at,end=at)
        u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
        u.emu_start(0x40000530,0x4000053a,count=200_000_000)
        assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a,'boot incomplet'
        assert bytes(u.mem_read(origin,len(code)))==expected,'module modifie/absent au vrai boot'
        r.call(0x4007929c)
        assert bytes(u.mem_read(origin,len(code)))==expected,'cache disque ecrase module'
        print('PASS vrai boot navigateur et constructeur cache : module exact, copie sans allocation',flush=True)
        r.w32(r.s['br_old_key'],0)
    else:u.mem_write(origin,bytes(code))
    def invalid(uc,access,address,size,value,user):
        print('FAULT',hex(uc.reg_read(mk.UC_M68K_REG_PC)),hex(address),size,'heap',hex(r.heap),flush=True);return False
    u.hook_add(UC_HOOK_MEM_INVALID,invalid)
    def call(name,*args):
        u.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*args));u.reg_write(mk.UC_M68K_REG_A7,STACK)
        u.emu_start(r.s[name] if isinstance(name,str) else name,STOP,count=10_000_000)
        assert u.reg_read(mk.UC_M68K_REG_PC)==STOP,('retour',name,hex(u.reg_read(mk.UC_M68K_REG_PC)))
        assert u.reg_read(mk.UC_M68K_REG_A7)==STACK+4,('pile',name)
        return u.reg_read(mk.UC_M68K_REG_D0)
    def get(name):return r.r32(r.s[name])
    def put(name,v):r.w32(r.s[name],v)
    def key(code,flags=1):
        u.mem_write(EVENT,bytes(24));r.w32(EVENT+12,code);r.w32(EVENT+16,flags)
        return call('br_key_hook',EVENT)
    def audio(value=0):
        for lane in range(6):u.mem_write(0x80001858+128*lane,struct.pack('>32i',*([value*(lane+1)]*32)))
        call('br_audio')
        return [list(struct.unpack('>32i',bytes(u.mem_read(0x80001858+128*lane,128)))) for lane in range(6)]
    r.w32(0x40fe4178,0x93005000)
    popups=[]
    def make_string(args):r.w32(args[0],args[1]);return args[0]
    def popup_ctor(args):
        popups.append(r.string(r.r32(args[1])))
        return args[0]
    for at,fn in ((0x400f980c,make_string),(0x400747c0,popup_ctor),(0x400f7d5c,lambda args:0)):
        r.stubs[at]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    r.stubs[0x40076c04]=lambda args:0;u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40076c04,end=0x40076c04)
    r.w32(0x40149310,14400);r.w32(0x40a7883c,1)
    # Au repos : aucun buffer, audio bit-identique et aucune allocation.
    before=r.new_count;assert audio(12345)==[[12345*(i+1)]*32 for i in range(6)]
    assert r.new_count==before and not get('br_history')
    print('PASS repos : aucun historique/allocation, six canaux inchanges',flush=True)
    assert key(2)==2;assert key(16)==16;assert key(16,0)==16
    assert key(4)==0 and get('br_keys')==3 and get('br_history')
    assert r.new_count==before+1
    for code in range(16,32):
        assert key(code)==0 and r.r32(EVENT+12)==0
        assert get('br_requested')==code-16
        assert key(code,9)==0 and key(code,0)==0
    assert get('br_requested')==0xffffffff
    if 'br_popup' in r.s:assert popups==['1/64','1/48','1/32','1/24','1/16','1/12','1/8','1/6','3/16','1/4','1/3','3/8','1/2','2/3','3/4','1 BAR'],popups
    if 'br_popup' in r.s:print('PASS popup natif : seize divisions exactes, aucun doublon sur repeat/release',flush=True)
    assert key(16)==0;assert key(20)==0;assert get('br_requested')==4
    assert key(20,0)==0 and get('br_requested')==0
    # Un press TRIG reste possede jusqu'a sa release, meme apres le combo.
    assert key(2,0)==2 and get('br_requested')==0xffffffff
    assert key(16,0)==0 and get('br_owned')==0
    assert key(4,0)==0;assert key(4)==4;assert key(2)==2
    assert get('br_keys')==3;assert key(4,0)==4
    assert get('br_requested')==0xffffffff
    key(2,0)
    print('PASS TRACK/RETRIG dans les deux ordres, 16 divisions, releases, repeats et retour au dernier TRIG tenu',flush=True)
    # Remplir l'historique avec des valeurs propres a chaque piste.
    key(2);key(4);hist=get('br_history');put('br_blocks',4096)
    for lane in range(6):u.mem_write(hist+2*N*lane,struct.pack('>h',1000*(lane+1))*N)
    r.w32(0x8000184c,0);key(18)
    for _ in range(100):out=audio(1000*32768)
    assert get('br_length')==3000 and get('br_wet')==65536
    # Apres le fondu initial : six pistes, amplitudes distinctes, memes positions.
    out=audio()
    for lane in range(6):assert all(v==1000*(lane+1)*32768 for v in out[lane]),(lane,out[lane][:3])
    # Une release de chacun des deux modificateurs termine en 64 echantillons.
    key(4,0);audio(200);audio(200);assert get('br_wet')==0
    assert audio(200)==[[200*(i+1)]*32 for i in range(6)]
    key(2,0);key(18,0)
    print('PASS 1/32 : six boucles synchrones ; release RETRIG, retour audio normal en 64 echantillons',flush=True)
    key(2);key(4);key(18);audio();audio();key(2,0);audio(300);audio(300)
    assert get('br_wet')==0 and audio(300)==[[300*(i+1)]*32 for i in range(6)]
    key(18,0);key(4,0)
    print('PASS release TRACK termine egalement la repetition ; touches possedees nettoyees',flush=True)
    # Stop et changement de projet annulent ; pas de reprise surprise.
    key(2);key(4);key(18);audio();r.w32(0x40a7883c,0);audio();audio()
    assert get('br_wet')==0 and get('br_cancel')==1
    r.w32(0x40a7883c,1);audio();assert get('br_wet')==0
    key(18,0);key(4,0);key(2,0)
    r.w32(0x40a78888,0x41400000);key(2);key(4);key(18);audio()
    r.w32(0x40a78888,0x41500000);audio();audio();assert get('br_wet')==0
    key(18,0);key(4,0);key(2,0)
    print('PASS Stop/projet different annulent, sans repetition au redemarrage transport',flush=True)
    if case:
        cac=next((t for t in case['tweaks'] if 'cac_keys' in t.get('symbols',{})),None)
        if cac:
            cs={k:int(v,16) for k,v in cac['symbols'].items()};u.mem_write(cs['cac_mask'],b'\x15')
            r.stubs[0x40024078]=lambda a:0;u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40024078,end=0x40024078)
            key(2);key(4)
            for trig in range(16,32):
                key(trig);assert r.r32(EVENT+12)==0;call(cs['cac_keys'],0x93000000,EVENT)
                key(trig,0);call(cs['cac_keys'],0x93000000,EVENT)
            key(4,0);key(2,0)
            assert bytes(u.mem_read(cs['cac_mask'],1))==b'\x15'
            u.mem_write(cs['cac_mask'],b'\0')
            print('PASS vrais handlers Control All : 16 press/release de repeat sans changer le masque',flush=True)
    # Tempo lent / tres rapide : divisions valides, historiques bornes.
    for tempo in (1,3600,14400,65520):
        key(2);key(4);r.w32(0x40149310,tempo)
        for step in range(16):
            put('br_valid',0);put('br_wet',0);key(16+step);audio()
            assert 0<get('br_length')<=N-4096,(tempo,step,get('br_length'))
            key(16+step,0)
        key(4,0);key(2,0)
    print('PASS 16 divisions x quatre tempos : tailles dans les bornes, aucun diviseur nul',flush=True)
    # Regression materielle : les 64 selections Control All filtrent l'audio.
    old_mask=get('br_mask_address');put('br_mask_address',0x93072000)
    hist=get('br_history')
    for lane in range(6):u.mem_write(hist+2*N*lane,struct.pack('>h',1000*(lane+1))*N)
    r.w32(0x40149310,14400);key(2);key(4);key(18)
    for mask in range(64):
        u.mem_write(0x93072000,bytes([mask]));put('br_blocks',8192)
        put('br_valid',1);put('br_active',2);put('br_length',3000);put('br_start',8192*32-6000)
        for _ in range(3):out=audio(333)
        for lane in range(6):
            wanted=(333 if mask&(1<<lane) else 1000*32768)*(lane+1)
            assert all(v==wanted if mask&(1<<lane) else abs(v-wanted)<=511 for v in out[lane]),('mask',mask,lane,out[lane][:3],wanted)
    key(18,0);key(4,0);key(2,0);audio();audio();put('br_mask_address',old_mask)
    print('PASS 64 masques Control All : exclus restent live, inclus bouclent ; changements avec fondu',flush=True)
    # Le handler TRACK doit prendre les touches AVANT cac_keys, pas apres.
    leds=[];old_led_calls=[]
    for at,fn in ((0x400cfaf4,lambda args:0x93073000),(0x40005f86,lambda args:leds.append(args[:4]) or 0),(0x40023d8c,lambda args:old_led_calls.append(args[:3]) or 0)):
        r.stubs[at]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    if not get('br_old_track_keys'):put('br_old_track_keys',0x40024078);put('br_old_track_leds',0x40023d8c)
    key(2);key(4)
    for trig in range(16,32):
        u.mem_write(EVENT,bytes(24));r.w32(EVENT+12,trig);r.w32(EVENT+16,1)
        assert call('br_track_keys',0x93000000,EVENT)==1 and get('br_requested')==trig-16
        leds.clear();r.w32(0x93074000,0x80000000)
        call('br_track_leds',0x93000068,0xffffffff,0x93074000)
        assert [(v[1],v[2]) for v in leds]==[(i+1,2 if i==trig-16 else 1) for i in range(16)]
        assert r.r32(0x93074000)==0x8001fffe
        r.w32(EVENT+12,trig);r.w32(EVENT+16,0);assert call('br_track_keys',0x93000000,EVENT)==1
    assert not old_led_calls,'options Control All presentes dans combo'
    key(4,0);leds.clear();call('br_track_leds',0x93000068,0xffffffff,0x93074000)
    assert len(old_led_calls)==1
    if case and cac:
        assert len(leds)==6,'choix Control All non restaures'
        assert bytes(u.mem_read(cs['cac_mask'],1))==b'\0'
        r.w32(EVENT+12,16);r.w32(EVENT+16,1);call('br_track_keys',0x93000000,EVENT)
        assert bytes(u.mem_read(cs['cac_mask'],1))==b'\x01','config ordinaire TRACK perdue'
        r.w32(EVENT+12,16);r.w32(EVENT+16,0);call('br_track_keys',0x93000000,EVENT)
        u.mem_write(cs['cac_mask'],b'\0')
    key(2,0)
    print('PASS vue TRACK directe : 16 divisions prioritaires, LEDs de division, options normales restaurees a la release',flush=True)
    # Compter les instructions propres : pas une estimation de cycles CPU.
    count=[0]
    def instruction(uc,pc,size,user):count[0]+=1
    meter=u.hook_add(UC_HOOK_CODE,instruction,begin=origin,end=origin+len(data['hex'])//2)
    r.w32(0x40149310,14400);key(2);key(4);key(18);audio();audio();count[0]=0;audio();six=count[0]
    key(18,0);key(4,0);key(2,0);audio();audio();count[0]=0;audio();idle=count[0]
    u.hook_del(meter)
    print('MESURE instructions propres/bloc : repos apres allocation',idle,'; repetition',six,'; cycles materiels non mesures',flush=True)
    # Les cotes stereo optionnels restent lies a leur piste, sans retour FX.
    old_history,old_side,old_on=get('br_history'),get('br_side'),get('br_side_on')
    u.mem_map(0x94000000,0x400000);put('br_history',0x94000000)
    put('br_side',0x93070000);put('br_side_on',0x93071000)
    u.mem_write(0x93071000,struct.pack('>6I',*([1]*6)))
    put('br_valid',0);put('br_wet',0);key(2);key(4);key(18)
    for _ in range(100):
        for lane in range(6):u.mem_write(0x93070000+128*lane,struct.pack('>32i',*([300*(lane+1)*32768]*32)))
        audio(1000*32768)
    for lane in range(6):u.mem_write(0x93070000+128*lane,bytes(128))
    audio()
    for lane in range(6):assert struct.unpack('>32i',bytes(u.mem_read(0x93070000+128*lane,128)))==(300*(lane+1)*32768,)*32
    put('br_mask_address',0x93072000);u.mem_write(0x93072000,b'\x15')
    for _ in range(3):
        for lane in range(6):u.mem_write(0x93070000+128*lane,struct.pack('>32i',*([77*(lane+1)]*32)))
        audio(333)
    for lane in range(6):
        side=struct.unpack('>32i',bytes(u.mem_read(0x93070000+128*lane,128)))
        assert all(v==77*(lane+1) if 0x15&(1<<lane) else abs(v-300*(lane+1)*32768)<=511 for v in side),('stereo mask',lane,side[:3])
    put('br_mask_address',old_mask)
    key(4,0);key(2,0);key(18,0);audio();audio()
    put('br_history',old_history);put('br_side',old_side);put('br_side_on',old_on)
    print('PASS six cotes stereo : captures distinctes et masque Control All identique au canal principal',flush=True)
    # Les frontaux gardent les arguments et registres preserves du natif.
    seen=[];gain=get('br_old_gain')
    r.stubs[gain]=lambda args:seen.append(args[0]) or 0x5566
    u.hook_add(UC_HOOK_CODE,r.stub,begin=gain,end=gain)
    regs=[getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]
    for i,reg in enumerate(regs):u.reg_write(reg,0x12340000+i)
    assert call('br_gain_hook',0x93090000)==0x5566 and seen==[0x93090000]
    assert [u.reg_read(reg) for reg in regs]==[0x12340000+i for i in range(6)]
    old_key=get('br_old_key');put('br_old_key',0x9300c000)
    r.stubs[0x9300c000]=lambda args:r.r32(args[0]+12)
    u.hook_add(UC_HOOK_CODE,r.stub,begin=0x9300c000,end=0x9300c000)
    assert key(12)==12;put('br_old_key',old_key)
    print('PASS chaines gain/clavier anterieures : arguments, resultat, registres et pile preserves',flush=True)
    # Allocation ratee / IPL : rester vivant, aucune allocation audio.
    put('br_history',0);r.fail_new=r.new_count+1;key(2);key(4);assert not get('br_history')
    count=r.new_count;audio(99);assert r.new_count==count
    key(4,0);key(2,0);r.fail_new=False;u.reg_write(mk.UC_M68K_REG_SR,0x2100)
    key(2);key(4);assert not get('br_history');u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    print('PASS memoire indisponible/IPL : bypass, aucune allocation dans le rendu',flush=True)
    if a.meter:
        assert 'br_load_address' in r.s and 'br_avg_address' in r.s
        key(4,0);key(2,0)
        put('br_history',0x94000000)  # historique fixture deja mappe, sans nouvelle allocation
        put('br_load_address',0x9307e000);put('br_avg_address',0x9307e004)
        put('br_fading_address',0);put('br_stolen_address',0)
        r.w32(0x9307e000,232);r.w32(0x9307e004,194)
        key(2);key(4);audio(42);r.w32(0x9307e000,300);audio(42)
        assert get('br_load_peak')==300
        key(4,0);assert popups[-1]=='CPU 75%/117%',popups[-1]
        key(2,0);put('br_fading_address',0x9307e010);put('br_stolen_address',0x9307e020)
        u.mem_write(0x9307e010,bytes([0,8,0,0,0,0]));u.mem_write(0x9307e020,bytes([0,0,0,0,0,1]))
        key(2);key(4);audio(42)
        assert get('br_cut_seen')==34
        assert bytes(u.mem_read(0x9307e010,6))==bytes([0,8,0,0,0,0])
        assert bytes(u.mem_read(0x9307e020,6))==bytes([0,0,0,0,0,1])
        u.mem_write(0x9307e010,bytes(6));u.mem_write(0x9307e020,bytes(6));audio(42)
        key(4,0);assert popups[-1]=='CPU 75%/117% CUT 2',popups[-1]
        key(2,0);key(2);key(4);audio(42);key(4,0)
        assert popups[-1]=='CPU 75%/117% CUT 0',popups[-1]
        if 'br_filter_f_address' in r.s:
            for name,offset,value in [('f',0x100,3538),('q',0x120,0),('mk',0x140,4096),('modes',0x160,0x20)]:
                put('br_filter_'+name+'_address',0x9307e000+offset);r.w32(0x9307e000+offset+20,value)
            key(2,0);key(1);key(2);key(4);key(4,0)
            assert popups[-1]=='6M0020 F3538Q0K4096',popups[-1]
            key(2,0);key(2);key(4)
            for lane in range(6):
                r.w32(0x9307e100+lane*4,1000+lane);r.w32(0x9307e120+lane*4,0);r.w32(0x9307e140+lane*4,4096);r.w32(0x9307e160+lane*4,0x20)
                key(16+lane);assert popups[-1]==str(lane+1)+'M0020 F'+str(1000+lane)+'Q0K4096',popups[-1]
                assert get('br_requested')==0xffffffff
                key(16+lane,0)
            key(4,0);assert popups[-1]=='6M0020 F1005Q0K4096'
            key(2,0);put('br_filter_f_address',0);key(2);key(4);key(4,0)
            assert popups[-1]=='FILTER OFF',popups[-1]
            key(1,0)
        put('br_fading_address',0);put('br_stolen_address',0)
        key(2,0);put('br_load_address',0);put('br_avg_address',0)
        print('PASS diagnostic : moyenne/pic Q8, CUT distinct cumulatif/reset, flags regulateur non modifies, popup UI seulement',flush=True)
    print('LIMITES : pas de mesure CPU materielle, ni clavier physique ; prototype experimental')
if __name__=='__main__':main()
