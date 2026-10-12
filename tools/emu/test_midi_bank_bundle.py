#!/usr/bin/env python3
"""Note 57 : boot réel du bundle TG-ST/LFO 2/MIDI, puis hooks placés.

Décompression native, copie et remise à zéro exécutées sur l'image composée.
Les caches sont observés par modèle, Unicorn n'émule pas leur cohérence.
Pas encore de preuve du scheduler complet ou de persistance sur disque.
"""
import argparse
import pathlib
import struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_BLOCK,m68k_const as mk
import gen_midi_bank_bundle as gen
import gen_syntakt_engines as gs
import syntakt
from test_seq_gen_menu import Rig,STACK,EVENT,RAW
from test_macro_syntakt import chord_at,chord_tables
from test_midi_lane_scheduler import prove as prove_scheduler


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt',required=True)
    ap.add_argument('--model-tg',required=True);ap.add_argument('--cross',default='m68k-elf-')
    ap.add_argument('--pattern-banks',action='store_true')
    ap.add_argument('--stock-display',action='store_true')
    ap.add_argument('--stereo-usb',action='store_true')
    ap.add_argument('--cache-blocks',type=int,choices=(6,7),default=6)
    ap.add_argument('--lfo-cc',action='store_true')
    ap.add_argument('--storage',action='store_true',help='Raccordement stockage prototype non publié')
    ap.add_argument('--conditions',action='store_true')
    ap.add_argument('--retrigger',action='store_true',help='Raccordement retrigger/arp B prototype')
    args=ap.parse_args()
    if args.lfo_cc:args.cache_blocks=8 if args.conditions else 7
    stock=gen.main_os_from_syx(args.cycles)
    tweak,chosen,image=gen.generate(stock,args.syntakt,args.model_tg,args.cross,args.pattern_banks,args.stock_display,not args.stereo_usb,args.cache_blocks,args.lfo_cc,args.storage,args.retrigger,args.conditions)
    if args.storage or args.retrigger:
        import build
        assert build.payload_image(tweak,bytes.fromhex(tweak['append']['parts'][0]['hex']))==bytes.fromhex(tweak['append']['compressed_hex'])
        print('ok : stockage précompressé vérifié, marge image',build.END_LIMIT-build.BASE-len(image),'octets')
    s={k:int(v,16) for k,v in tweak['symbols'].items()}
    r=Rig(stock,{'writes':[]},{'writes':[],'symbols':tweak['symbols']});u=r.u
    lo=0x4019b590;hi=0x423380b0;start=s['ML_BANK_START'];end=s['ML_BANK_END']
    u.mem_write(lo,b'\xa5'*(hi-lo))
    u.mem_write(gen.build.BASE,image)
    u.mem_map(0x46700000,0x100000);u.mem_write(0x46700000,b'\xa5'*0x100000)
    u.mem_map(0x80000000,0x10000)
    for src,srcend,dest in gs.CY_SRAM_INIT:
        u.mem_write(dest,image[src-gen.build.BASE:srcend-gen.build.BASE])
    keep={getattr(mk,'UC_M68K_REG_'+name):0x12340000+i for i,name in enumerate(
          ('D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6'))}
    for reg,value in keep.items():u.reg_write(reg,value)
    u.reg_write(mk.UC_M68K_REG_A7,STACK);u.reg_write(mk.UC_M68K_REG_SR,0x2700)
    dirty=set();invals=[];faults=[];copied=[0]
    def write(u,access,addr,size,value,data):
        dirty.update(range(addr>>4,((addr+size-1)>>4)+1));copied[0]+=size
    def block(u,addr,size,data):
        if any(line in dirty for line in range(addr>>4,((addr+size-1)>>4)+1)):faults.append(addr)
    handles=[u.hook_add(UC_HOOK_MEM_WRITE,write,begin=start,end=end-1),
             u.hook_add(UC_HOOK_BLOCK,block,begin=start,end=end-1)]
    def cache(u,addr,size,data):
        assert u.reg_read(mk.UC_M68K_REG_D0)==0x000cc100
        assert copied[0]==end-start
        dirty.clear();invals.append(addr)
    # Le seul MOVEC CACR du chargeur, opcode vérifié avant observation.
    loader=s['ml_boot_copy']
    stub=next(bytes.fromhex(w['new']) for w in tweak['writes'] if gen.build.BASE+w['off']==loader)
    at=stub.index(bytes.fromhex('4e7b0002'))
    handles.append(u.hook_add(UC_HOOK_CODE,cache,begin=loader+at,end=loader+at))
    u.emu_start(0x40000530,0x4000053a,count=80_000_000)
    assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a,'boot sans reprise'
    assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-4
    assert r.r32(STACK-4)==0x40000536
    assert all(u.reg_read(reg)==value for reg,value in keep.items())
    assert invals and not faults and copied[0]==end-start
    for handle in handles:u.hook_del(handle)
    # Les detours Genie doivent survivre au vrai boot TG/Syntakt.
    catalog=gen.build.load_catalog()['model-cycles_OS1.13'][1]
    sg=catalog['scale-gen-st-queued']['symbols'];menu=int(sg['sg_menu_key'],16)
    for ours in ('ml_genie_generate','ml_genie_undo'):
        call=b'\x4e\xb9'+struct.pack('>I',s[ours])
        sites=[at for at in range(menu,menu+0x400,2) if image[at-gen.build.BASE:at-gen.build.BASE+6]==call]
        assert len(sites)==1,(ours,sites)
        assert bytes(u.mem_read(sites[0],6))==call,('detour Genie perdu au boot',ours)
    print('ok : detours Generate/Undo B présents après le vrai boot TG/Syntakt')
    bank=bytes.fromhex(tweak['append']['parts'][0]['hex'])
    assert bytes(u.mem_read(start,len(bank)))==bank
    tgstart=s['ML_TG_START']
    assert bytes(u.mem_read(tgstart,start-tgstart))==image[tgstart-gen.build.BASE:start-gen.build.BASE]
    assert not any(u.mem_read(lo,tgstart-lo))
    assert not any(u.mem_read(end,hi-end))
    st=next(t for t in chosen if t['id'].startswith('syntakt-tg-'))
    st_img=syntakt.dsp_image(args.syntakt)
    expected=bytearray(gen.build.payload_runtime(st,stock,st_img))
    # Le second étage natif restaure les ondes CHORD depuis SRAM ; elles
    # sont volontairement absentes du flux compressé (preuve note 50).
    chord=chord_tables(stock);offset=chord_at(st,{'st_img':st_img})-int(st['append']['dest'],16)
    expected[offset:offset+len(chord)]=chord
    assert bytes(u.mem_read(int(st['append']['dest'],16),len(expected)))==expected
    print('ok : vrai boot ST puis MIDI, décompression exacte, copie après décompression, TG et banque conservés')
    print('ok : tampon nul/disque et reste BSS remis à zéro, invalidation cache avant exécution, registres/pile et reprise natifs')
    # Réinitialisation réelle du cache après boot : seules les voies disque
    # non réservées doivent être atteignables depuis sa tête LRU.
    before=bytes(u.mem_read(tgstart,end-tgstart))
    r.call(0x4007929c)
    node=r.r32(0x401eb894);nodes=[]
    while node:
        assert node not in nodes
        nodes.append(node);node=r.r32(node+12)
    assert nodes==[0x401eb750+20*i for i in range(args.cache_blocks,16)]
    assert bytes(u.mem_read(tgstart,end-tgstart))==before
    print('ok : réserve cache',args.cache_blocks,'blocs, liste native',len(nodes),'blocs après boot, payload intact')

    # Pliage réel TG dans le bundle : toutes gammes/tonalités/notes, ABI.
    tg=gen.symbols(args.cross,pathlib.Path(args.model_tg)/'build/_b.elf')
    scales=(None,(0,2,4,5,7,9,11),(0,2,3,5,7,8,10),
            (0,2,3,5,7,9,10),(0,2,4,7,9))
    for scale,table in enumerate(scales):
      u.mem_write(tg['scale_state'],bytes([scale]))
      for root in range(12):
        u.mem_write(tg['key_state'],bytes([root]))
        for note in range(128):
          expected=note
          if table is not None and note!=127:
            octave,degree=divmod(note-52,len(table))
            expected=48+12*octave+table[degree]+root
          u.reg_write(mk.UC_M68K_REG_D0,note)
          assert r.call('mlp_scale_note')==expected&0xffffffff,(scale,root,note)
    u.mem_write(tg['scale_state'],b'\0');u.mem_write(tg['key_state'],b'\0')
    print('ok : pliage clavier TG réel, cinq gammes × douze tonalités × 128 notes')
    # Contexte créé depuis la même image après boot, pas de relocation de fixture.
    # État scheduler UI fourni : son initialisation OS complète reste hors preuve.
    r.w32(0x4049fd60,0x422feec8+24)
    u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    assert r.call('mm_prepare')==1
    merge_ctx=r.r32(s['mm_context'])
    assert merge_ctx and bytes(u.mem_read(merge_ctx,8256))==bytes(8256)
    assert r.call('ml_prepare')==1
    assert r.call('ml_worker_prepare')==1
    ctx=r.r32(s['ml_context']);worker=r.r32(s['ml_worker_context'])
    assert ctx and worker
    if args.pattern_banks:
        r.w32(0x40a7887c,0x93090000)
        r.w32(0x93090000+30706,0)
    assert bytes(u.mem_read(ctx,8))==bytes([1,0,6,4,16,2,0,0])
    assert all(u.mem_read(ctx+264*lane+2,1)[0]==lane+6 for lane in range(6))
    assert r.r32(worker+12)==ctx+1584
    print('ok : code placé crée contexte/six canaux 7..12 et tâche native après remise à zéro')
    # Getter réel : banque -> SCRAMBLE -> Sequence Genie -> Model-TG.
    r.w32(0x40fe4178,1)
    r.w32(0x93005030,0x93005100);r.w32(0x93005128,0x93005200)
    u.mem_write(0x93005200,b'\x20\x3c'+struct.pack('>I',0x93005300)+b'\x4e\x75')
    r.w32(0x93005304,5)
    saved=bytes(u.mem_read(RAW,722));stamp=0
    def key(code,flags=1):
        nonlocal stamp
        stamp+=1;r.event(code,flags,stamp)
        values=[r.call(0x4007240c,EVENT) for _ in range(3)]
        assert len(set(values))==1,values
        return values[0]
    for code in range(33):
        r.w32(s['TG_set_held'],0)
        assert key(code)==code
    r.w32(s['TG_set_held'],0)
    assert key(13,3)==13 and r.r32(s['TG_set_held'])==1
    assert key(2,3)==0
    obj=r.r32(s['mlp_obj']);assert obj and r.r32(s['mlp_track'])==5
    assert r.r32(s['TG_mod_used'])==1
    assert key(2,11)==0 and r.r32(s['mlp_obj'])==obj
    assert key(2,2)==0 and key(13,2)==0
    assert not r.r32(s['TG_set_held'])
    assert key(13,3)==13
    r.event(13,3,stamp)
    assert r.call('mlp_menu_key',obj,EVENT)==0 and r.r32(s['mlp_obj'])==obj
    # La fermeture native marque +48 ; la destruction vient du gestionnaire
    # UI, qui n'est pas exécuté dans cette fixture de présentation.
    assert key(2,3)==0 and u.mem_read(obj+48,1)[0]==1
    r.call('mlp_dtor1',obj)
    assert not r.r32(s['mlp_obj'])
    assert key(2,2)==0 and key(13,2)==0
    assert r.r32(s['ml_context'])==ctx
    assert bytes(u.mem_read(RAW,722))==saved and r.r32(0x93005304)==5
    print('ok : chaîne complète des getters, combo FUNC+SETTINGS+TRACK idempotent, demande fermeture native et contexte conservé')
    # Routeur OS réel de cette image, verrous et writers physiques simulés.
    output=[];mode=[0]
    def install(at,fn):
        r.stubs[at]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    install(0x40044df8,lambda a:mode[0])
    for at,port in ((0x40001100,'DIN'),(0x40003396,'USB')):
        install(at,lambda a,port=port:output.append((port,bytes(u.mem_read(a[1],a[0])))) or 0)
    for at in (0x400032ca,0x400032da):install(at,lambda a:0)
    def forbidden(u,at,size,data):raise AssertionError('chemin sonore atteint : '+hex(at))
    for at in (0x4005894a,0x400548ce,0x40058e28):
        u.hook_add(UC_HOOK_CODE,forbidden,begin=at,end=at)
    r.w32(0x40fe4228,1)
    # Un CC reçu seul doit réveiller la tâche, sans notes en attente.
    u.reg_write(mk.UC_M68K_REG_SR,0x2400)
    assert r.call('mm_feed',merge_ctx,0xb6)==0
    assert r.call('mm_feed',merge_ctx,74)==0
    assert r.call('mm_feed',merge_ctx,100)==1
    r.w32(worker+8,0)
    r.call('ml_worker_kick')
    assert r.r32(worker+8)==1
    u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    r.call('ml_worker_once',worker)
    assert output==[('DIN',bytes([0xb6,74,100]))]
    assert r.r32(merge_ctx+16)==0 and r.r32(worker+8)==0
    print('ok : allocation merger après boot, CC seul réveille le worker, sortie DIN hors IRQ')
    for thru in (0,1):
        mode[0]=thru;output.clear()
        for lane in range(6):
            assert r.call('ml_step',ctx+1584,lane,((0x96+lane)<<24)|(60<<16)|(100<<8)|4,1)==1
        for lane in range(6):r.call('ml_stop',ctx+1584,lane)
        assert r.call('ml_service',ctx+1584,8)==8
        assert r.call('ml_service',ctx+1584,8)==4
        packets=[bytes([0x96+i,60,100]) for i in range(6)]+[bytes([0x86+i,60,0]) for i in range(6)]
        assert output==[(port,packet) for packet in packets for port in ('DIN','USB')]
    assert bytes(u.mem_read(RAW,722))==saved
    print('ok : Select All Live MIDI Out+Thru conservé, douze paquets DIN/USB en OUT et THRU, aucun chemin sonore')
    # Les sites Start/audio placés exécutent leurs instructions stock ;
    # l'état Play et l'heure restent fournis, pas le chemin Play complet.
    output.clear()
    for lane in range(6):assert r.call('ml_edit',ctx,lane,0,3,1)==1
    due=123456;r.w32(0x40a78628,due)
    u.reg_write(mk.UC_M68K_REG_A0,0x40a78628)
    u.reg_write(mk.UC_M68K_REG_D6,0);u.reg_write(mk.UC_M68K_REG_SR,0x2700)
    u.emu_start(0x40054686,0x4005468c,count=2000)
    assert r.r32(0x80001848)==due and r.r32(s['ml_start_context'])==ctx
    def tick(now,playing):
        r.w32(0x8000184c,now);r.w32(0x40a7883c,playing)
        u.reg_write(mk.UC_M68K_REG_SR,0x2500)
        u.emu_start(0x400594a8,0x400594ae,count=20000)
        assert u.reg_read(mk.UC_M68K_REG_PC)==0x400594ae
    tick(due-1,1);assert not r.r32(ctx+1584) and not output
    tick(due,1);assert r.r32(ctx+1584)==6 and not output
    u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    r.call(0x40001aca,worker);assert r.call('ml_worker_once',worker)==6
    assert output==[(port,bytes([0x96+i,60,100])) for i in range(6) for port in ('DIN','USB')]
    tick(due+1,0);assert r.r32(ctx+1584)==6 and len(output)==12
    u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    r.call(0x40001aca,worker);assert r.call('ml_worker_once',worker)==6
    assert output[12:]==[(port,bytes([0x86+i,60,0])) for i in range(6) for port in ('DIN','USB')]
    assert bytes(u.mem_read(RAW,722))==saved
    print('ok : sites Start/audio placés, attente échéance, six voies et Stop ; aucun writer IRQ, consommateur IPL0')
    if args.pattern_banks:
        # Le code placé doit suivre l'identité au vrai site audio, sans
        # confondre la banque affichée avec celle en lecture.
        r.w32(0x93090000+30706,1)
        assert r.call('ml_bank_ui_sync') == 1
        bank_b=r.r32(s['ml_pattern'])
        assert bank_b != ctx
        assert r.call('ml_edit',bank_b,0,0,0,77)==1
        assert r.call('ml_edit',bank_b,0,0,3,1)==1
        output.clear()
        tick(due+2,1)
        assert r.r32(s['ml_play_pattern'])==bank_b
        u.reg_write(mk.UC_M68K_REG_SR,0x2000)
        r.call('ml_worker_once',worker)
        assert output==[(port,bytes([0x96,77,100])) for port in ('DIN','USB')]
        r.w32(0x93090000+30706,0)
        tick(due+3,1)
        assert r.r32(s['ml_play_pattern'])==ctx
        u.reg_write(mk.UC_M68K_REG_SR,0x2000)
        r.call('ml_worker_once',worker)
        assert output[2:4]==[(port,bytes([0x86,77,0])) for port in ('DIN','USB')]
        tick(due+4,0)
        u.reg_write(mk.UC_M68K_REG_SR,0x2000)
        r.call('ml_worker_once',worker)
        assert r.call('ml_bank_ui_sync')==1 and r.r32(s['ml_pattern'])==ctx
        print('ok : banques par pattern dans le bundle placé, changement au site natif, ordre DIN/USB exact')
    if args.conditions:
        # Exécuter le chemin compact publié et le helper placé dans le masque.
        assert s['ml_condition_eval'] < s['ML_BANK_START']
        at=s['ml_condition_eval']
        assert bytes(u.mem_read(at,16))==image[at-gen.build.BASE:at-gen.build.BASE+16]
        private=0x930e1000;runtime=0x930e0000
        r.call('ml_init',private);r.call('ml_edit',private,0,0,3,1)
        settings=r.call('ml_repeat_pattern_prepare',private)
        assert settings
        r.w32(s['ml_repeat_play_settings'],settings)
        for encoded,fill,expected in ((0,0,1),(1,0,0),(101,0,1),(102,0,0),(102,1,1),(103,0,1),(103,1,0)):
            u.mem_write(runtime,bytes(320));u.mem_write(s['ml_repeat_states'],bytes(120))
            u.mem_write(settings+15,bytes((encoded,)))
            r.w32(s['ml_cond_fill'],fill)
            u.mem_write(0x40fde812,bytes(6));u.mem_write(0x40fde818,b'\0')
            u.reg_write(mk.UC_M68K_REG_SR,0x2500)
            r.call('ml_pattern_tick',runtime,private,0,0)
            assert bool(r.r32(runtime))==bool(expected),(encoded,fill,r.r32(runtime))
        # FILL latch natif et état momentané natif de la voie sont lus sans écriture.
        for addr in (0x40fde818,0x40fde812):
            u.mem_write(runtime,bytes(320));u.mem_write(s['ml_repeat_states'],bytes(120))
            r.w32(s['ml_cond_fill'],0);u.mem_write(settings+15,b'\x66')
            u.mem_write(addr,b'\1');r.call('ml_pattern_tick',runtime,private,0,0)
            assert r.r32(runtime)==1
            assert u.mem_read(addr,1)[0]==1
            u.mem_write(addr,b'\0')
        print('ok : vrai build compact, helper après boot, chance/héritage/FILL et inverse, latch natif, aucun état audio modifié')
    u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    # Réexécuter la preuve wait/post/scheduler avec le CODE placé du bundle.
    prove_scheduler(r)
    print('NOTE : TRAP/RTE adaptés ; timing physique, chemin Play complet et sauvegarde restent à valider')


if __name__=='__main__':main()
