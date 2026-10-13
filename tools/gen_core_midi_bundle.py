#!/usr/bin/env python3
"""Note65 : banque MIDI complète raccordée au noyau performance autonome.

--cycles OS1.13.syx --model-tg CLONE --output JSON [--check]. Réutilise les
sources et hooks du candidat Test3, sans sampler ni décompression Syntakt.
Aucun flasher existant modifié. Les données officielles ne sont pas exportées.
"""
import argparse,pathlib,struct,json,contextlib,io,shutil
import build,gen_performance_core as pc,gen_seq_gen as sg,gen_scramble as sc,gen_midi_bank_bundle as mb,sprites

def generate(stock,repo,cross=None):
    cross=cross or next((c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'as')),'m68k-linux-gnu-')
    core,blob,tg=pc.generate(stock,repo,cross)
    b,s=sg.compile_code(cross,tg,scroll=True,dynamics=True,advanced=True,sequence_only=True,queued=True)
    seq=sg.generate(stock,core,b,s,tg);seq['id']='scale-gen-st-queued';seq['conflicts']=[]
    slots,blobs,syms=sc.compile_code(cross,tg,s['sg_key'],steps=True,main=True)
    writes=[]
    def w(at,old,new):writes.append(dict(off=at-build.BASE,old=old.hex(),new=new.hex()))
    for (va,row,_),body in zip(slots,blobs):
     size,ptr,_,kept=row
     assert stock[va-build.BASE:va-build.BASE+size]==stock[kept-build.BASE:kept-build.BASE+size]
     w(ptr,struct.pack('>I',va),struct.pack('>I',kept));w(va,stock[va-build.BASE:va-build.BASE+len(body)],body)
    w(0x4007240c,b'\x4e\xf9'+struct.pack('>I',s['sg_key']),b'\x4e\xf9'+struct.pack('>I',syms['sc_key']))
    w(0x40054c0e,stock[0x40054c0e-build.BASE:0x40054c14-build.BASE],b'\x4e\xf9'+struct.pack('>I',syms['sc_steps_event']))
    scramble=dict(id='scramble-core',order=50,requires=['performance-core','scale-gen-st-queued'],conflicts=[],writes=writes,symbols={k:hex(v) for k,v in syms.items() if k.startswith('sc_')})
    cat=build.load_catalog();catalog=cat['model-cycles_OS1.13'][1];catalog[seq['id']]=seq
    catalog['scramble-st-gen-queued']=scramble
    chosen=sorted([core,seq,scramble]+[catalog[k] for k in ('latching-mute','trig-preview','lfo-secondary','midi-live-both','arp')],key=lambda t:t['order'])
    patched,_=build.apply_writes(stock,chosen);payload=build.build_payload(chosen,stock,None)[0]
    image=patched+payload
    # Même compilation MIDI, seuls les exports ABI sont remplacés.
    occupied=[(build.BASE+w['off'],build.BASE+w['off']+len(bytes.fromhex(w['new']))) for t in list(catalog.values())+chosen for w in t.get('writes',[])]
    free=[va for va,row in sprites.MASKS.items() if len(row)==4 and not any(va<hi and lo<va+row[0] for lo,hi in occupied)]
    loader=min(free,key=lambda va:(sprites.MASKS[va][0],va));free.remove(loader)
    start=(tg['blob_start']+len(blob)+15)&~15;limit=tg['blob_start']+4*16384;source=limit
    core['append']['size']=source-int(core['append']['at'],16)
    original=build.load_catalog;build.load_catalog=lambda:cat
    try:
     bank,stub,fragments,m=mb.compile_code(cross,tg,syms['sc_key'],start,limit,source,loader,free,pattern_banks=True,stock_display=True,lfo_cc=True,storage=True,repeat=True,conditions=True,extended_storage=True,audio_storage=True,working_storage=True,live_record=True)
    finally:build.load_catalog=original

    def finish():
        import aplib_dense
        nonlocal bank
        # Retirer le mapping PCM ACR1 du boot hérité : le noyau n'a aucun sampler.
        offset=m['ml_boot_clear']-start+8
        assert bank[offset:offset+10].hex()=='283c4c03e0004e7b4005',bank[offset:offset+10].hex()
        bank=bank[:offset]+b'\x4e\x71'*5+bank[offset+10:]
        packed=aplib_dense.pack(bank,depth=32)
        assert m['ML_BANK_END']<=source<=build.END_LIMIT-len(packed)
        patched,_=build.apply_writes(stock,chosen)
        cache_blocks=(m['ML_BANK_END']-tg['blob_start']+16383)//16384;blocks=1
        chain=[0x40000530];syms=m;blob=bank;merge_code=fragments
        lfo_cc=storage=repeat=conditions=extended_storage=audio_storage=working_storage=live_record=stock_display=True
        size,ptr,_,kept=sprites.MASKS[loader]
        writes=[]
        def write(at,new):
            old=patched[at-build.BASE:at-build.BASE+len(new)]
            assert len(old)==len(new)
            writes.append(dict(off=at-build.BASE,old=old.hex(),new=new.hex()))
        if repeat and not storage:
            at=0x4006a660
            assert image[at-build.BASE:at-build.BASE+8].hex()=="4cd7040c4fef0020"
            write(at,b"\x4e\xf9"+struct.pack(">I",syms["ml_repeat_project_hook"])+b"\x4e\x71")
        if storage:
            # Cibles natives exactes ; ordre boot/cache à valider avant publication.
            disk_hooks = [(0x4008b24a,'4fefffec48d7043c','ml_store_disk_read'),
                          (0x4008b3f6,'4fefffec48d7043c','ml_store_disk_write')] if extended_storage else [(0x400798c8,'4eb94008b24a','ml_store_disk_read')]
            for at,old,name in disk_hooks + [
                (0x4000f850,'4cd77c1c4fef0034','ml_store_save_hook'),
                (0x4006a660,'4cd7040c4fef0020','ml_store_load_hook')]:
                assert image[at-build.BASE:at-build.BASE+len(bytes.fromhex(old))].hex()==old
                op=b'\x4e\xb9' if at==0x400798c8 else b'\x4e\xf9'
                replacement=op+struct.pack('>I',syms[name])
                if len(bytes.fromhex(old))==8:replacement+=b'\x4e\x71'
                write(at,replacement)
        # Réserve optionnelle : sept blocs pour CC, huit pour conditions ; au moins huit blocs disque liés.
        if cache_blocks != blocks:
            write(0x400792f2,struct.pack('>I',0x401eb750+20*cache_blocks))
            write(0x400792bc,struct.pack('>I',0x401eb750+20*(cache_blocks+1)+16))
        redirect=sprites.redirect_write(loader)
        write(build.BASE+redirect['off'],bytes.fromhex(redirect['new']))
        write(loader,stub)
        for merge_mask,fragment in merge_code:
            redirect=sprites.redirect_write(merge_mask)
            write(build.BASE+redirect['off'],bytes.fromhex(redirect['new']))
            write(merge_mask,fragment)
        write(chain[0],b'\x4e\xf9'+struct.pack('>I',syms['ml_boot_copy']))
        assert image[0x4008e8c4-build.BASE:0x4008e8ce-build.BASE].hex()=='202f000441f94010abf8'
        write(0x4008e8c4,b'\x4e\xf9'+struct.pack('>I',syms['mlp_pulse_guard'])+b'\x4e\x71'*2)
        assert image[0x400012cc-build.BASE:0x400012d2-build.BASE].hex()=='2f02242f0008'
        write(0x400012cc,b'\x4e\xf9'+struct.pack('>I',syms['mm_rx']))
        if lfo_cc:
            expected=b'\x4e\xb9'+struct.pack('>I',int(catalog['lfo-secondary']['symbols']['lf2_dispatch'],16))
            assert image[0x400597c6-build.BASE:0x400597cc-build.BASE]==expected
            write(0x400597c6,b'\x4e\xb9'+struct.pack('>I',syms['mlcc_audio']))
        write(0x4007240c,b'\x4e\xf9'+struct.pack('>I',syms['ml_key']))
        write(0x40054686,b'\x4e\xf9'+struct.pack('>I',syms['ml_start_hook']))
        write(0x400594a8,b'\x4e\xb9'+struct.pack('>I',syms['ml_audio_hook']))
        write(0x40006a4a,b'\x4e\xf9'+struct.pack('>I',syms['ml_ui_hook'])+b'\x4e\x71')
        # Rediriger seulement les appels du menu ; les actions audio restent intactes.
        sg=catalog['scale-gen-st-queued']['symbols']
        for native,ours in (('sg_action_generate','ml_genie_generate'),('sg_action_undo','ml_genie_undo')):
            target=b'\x4e\xb9'+struct.pack('>I',int(sg[native],16))
            menu=int(sg['sg_menu_key'],16)
            sites=[at for at in range(menu,menu+0x400,2)
                   if patched[at-build.BASE:at-build.BASE+6]==target]
            assert len(sites)==1,(native,sites)
            write(sites[0],b'\x4e\xb9'+struct.pack('>I',syms[ours]))
        for native,ours in (('sg_pad','ml_genie_pad'),('sg_menu_key','ml_genie_menu_key'),('sg_render','sg_render')):
            target=b'\x20\x3c'+struct.pack('>I',int(sg[native],16))
            sites=[build.BASE+i for i in range(0,len(patched)-5,2) if patched[i:i+6]==target]
            assert len(sites)==1,sites
            write(sites[0],b'\x20\x3c'+struct.pack('>I',syms[ours]))
        # Le constructeur MACHINES ajoute le groupe de fermeture 2 ; garder B dessous.
        lo=int(sg['sg_o_allocate'],16);hi=int(sg['sg_o_done'],16)
        target=b'\x4e\xb9'+struct.pack('>I',0x4007700e)
        sites=[at for at in range(lo,hi,2) if patched[at-build.BASE:at-build.BASE+6]==target]
        assert len(sites)==1,sites
        write(sites[0],b'\x4e\xb9'+struct.pack('>I',syms['ml_genie_present']))
        if stock_display:
            for at,expected,name in ((0x4001b28a,'4eb940012412','mlp_stock_track'),
                                     (0x4001b774,'4eb940009c5a','mlp_stock_volume'),
                                     (0x4001b722,'2068001c4e90','mlp_stock_pan')):
                assert image[at-build.BASE:at-build.BASE+6].hex()==expected
                write(at,b'\x4e\xb9'+struct.pack('>I',syms[name]))
            assert image[0x4001b6ba-build.BASE:0x4001b6c4-build.BASE].hex()=='486a0001283c401117e0'
            write(0x4001b6ba,b'\x4e\xf9'+struct.pack('>I',syms['mlp_stock_track_label'])+b'\x4e\x71'*2)
        tweak=dict(id='midi-bank-bundle',order=60,name='Banque MIDI : bundle candidat',
                   description=['Six voies MIDI indépendantes, canaux fixes 7..12 ; réglages en RAM seulement.',
                                'Bindings du noyau autonome ; tools/gen_core_midi_bundle.py, note65.'],
                   device='Model:Cycles',os='1.13',section=3,status='experimental',
                   requires=[t['id'] for t in chosen],conflicts=[],writes=writes,
                   append=dict(at=hex(source),dest=hex(start),size=len(blob),
                               parts=[dict(dest=hex(start),hex=blob.hex())],reloc=[]),
                   symbols={k:hex(v) for k,v in syms.items()})
        if lfo_cc:tweak['append']['compress']='aplib'
        if storage or repeat:tweak['append']['compressed_hex']=packed.hex()
        final,_=build.apply_writes(stock,chosen+[tweak])
        append,_=build.build_payload(chosen+[tweak],stock,None)
        return tweak,chosen,final+append
    return finish()

def flatten(stock,tweak,chosen,image):
    """Un pack sélectionnable ; mêmes octets que la chaîne de composants validée."""
    patched,dirty=build.apply_writes(stock,chosen+[tweak]);assert image[:len(stock)]==patched
    runs=[]
    for off,changed in enumerate(dirty):
        if not changed:continue
        if runs and runs[-1][1]==off:runs[-1][1]+=1
        else:runs.append([off,off+1])
    writes=[dict(off=lo,old=stock[lo:hi].hex(),new=patched[lo:hi].hex()) for lo,hi in runs]
    at=build.BASE+len(stock);payload=image[len(stock):]
    pack=dict(id='performance-midi-core',order=30,name='Noyau autonome avec banque MIDI',device='Model:Cycles',os='1.13',section=3,status='experimental',
        description=['Slides, Scale Lock, mute verrouillé, aperçu de trig, Sequence Genie, SCRAMBLE, LFO2 et banque MIDI complète sans Model-TG.',
                     'Sauvegarde B/LFO A2/B, LFO CC et live recording du candidat Test3 ; sources partagées, nouveaux bindings. Hardware à vérifier. Note65.'],
        requires=[],conflicts=['performance-core','lfo-secondary','latching-mute','trig-preview','model-tg','model-tg-st'],writes=writes,
        append=dict(at=hex(at),dest=hex(at),size=len(payload),parts=[dict(dest=hex(at),hex=payload.hex())],reloc=[]),symbols=tweak['symbols'])
    with contextlib.redirect_stdout(io.StringIO()):
        p,_=build.apply_writes(stock,[pack]);tail,_=build.build_payload([pack],stock,None)
    assert p+tail==image
    return pack

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--model-tg',required=True);ap.add_argument('--output',required=True);ap.add_argument('--cross');ap.add_argument('--check',action='store_true');a=ap.parse_args()
    stock=sg.main_os_from_syx(a.cycles);t,chosen,image=generate(stock,a.model_tg,a.cross);pack=flatten(stock,t,chosen,image)
    text=json.dumps(pack,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
    if a.check:assert out.read_text()==text
    else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
    print('ok : pack MIDI sans Model-TG, quatre blocs cache ; marge image',build.END_LIMIT-build.BASE-len(image))
if __name__=='__main__':main()
