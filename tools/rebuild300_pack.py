"""Prototype du nouveau stockage : reference froide -> chargeur unique.

Ce prototype prouve l'architecture de chargement et son cout de stockage.
Il ne remplace pas l'audit de proprietaires/sections mortes et n'est pas une
reconstruction depuis les sources terminee. Aucun fichier public n'est touche.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
from removal_assets300 import compact_zero_runs
import aplib_grow

ENTRY=BASE+START+64
RUN=0x466f0000
STAGE_SOURCE=BASE+START+512
PACKED_SOURCE=BASE+START+4096
MAGIC=b'SMCLEAN1'


def sparse(at,raw):
    spans=[];start=None
    for offset in range(0,len(raw),256):
        used=any(raw[offset:offset+256])
        if used and start is None:start=offset
        if start is not None and (not used or offset+256>=len(raw)):
            end=offset if not used else len(raw)
            spans.append((at+start,raw[start:end]));start=None
    return spans


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--cycles',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--retire-components',action='store_true')
    parser.add_argument('--wizard-lock-scope',action='store_true')
    parser.add_argument('--retire-delegates',action='store_true')
    parser.add_argument('--retire-more-delegates',action='store_true')
    parser.add_argument('--wizard-sample-inherit',action='store_true')
    parser.add_argument('--standalone-shared-entries',action='store_true')
    parser.add_argument('--punch-work-gate',action='store_true')
    parser.add_argument('--release',default='3.00')
    parser.add_argument('--native-fx-unroll',action='store_true')
    parser.add_argument('--fx-wake-recovery',action='store_true')
    parser.add_argument('--diagnostic-midi',action='store_true')
    parser.add_argument('--exact-zero-voices',action='store_true')
    parser.add_argument('--eco-hall',action='store_true')
    parser.add_argument('--eco-hall-sparse',action='store_true')
    parser.add_argument('--hall-merged-gain',action='store_true')
    parser.add_argument('--delay-static',action='store_true')
    parser.add_argument('--filter-single-div',action='store_true')
    parser.add_argument('--filter-full-cache',action='store_true')
    parser.add_argument('--chord-second-fast',action='store_true')
    parser.add_argument('--filter-unroll',action='store_true')
    parser.add_argument('--fx-energy',action='store_true')
    parser.add_argument('--silent-commit-guard',action='store_true')
    parser.add_argument('--quality-economy',action='store_true')
    parser.add_argument('--idle-audit',action='store_true')
    parser.add_argument('--filter-half-rate',action='store_true')
    parser.add_argument('--restore-filter-capture',type=Path)
    parser.add_argument('--idle-scan-unroll',action='store_true')
    parser.add_argument('--panic-stock',action='store_true')
    parser.add_argument('--post-static',action='store_true')
    parser.add_argument('--post-dry-bypass',action='store_true')
    parser.add_argument('--output-monitor-fast',action='store_true')
    parser.add_argument('--upgrade-remote-data',action='store_true')
    parser.add_argument('--remote-panel',action='store_true')
    parser.add_argument('--deep-idle-wake',action='store_true')
    parser.add_argument('--deep-idle-stop',action='store_true')
    parser.add_argument('--stage-profile',action='store_true')
    parser.add_argument('--without-stage-profile',action='store_true')
    parser.add_argument('--sram-audio',action='store_true')
    parser.add_argument('--sram-audio-delay',action='store_true')
    parser.add_argument('--sram-delay-filter',action='store_true')
    parser.add_argument('--sram-full-delay',action='store_true')
    parser.add_argument('--sram-chord-priority',action='store_true')
    parser.add_argument('--chord-half-rate',action='store_true')
    parser.add_argument('--voice-filter-unroll',action='store_true')
    parser.add_argument('--native-finish',action='store_true')
    parser.add_argument('--phase-loop',action='store_true')
    parser.add_argument('--phase-sram',action='store_true')
    parser.add_argument('--native-biquad',action='store_true')
    parser.add_argument('--ui-fixes348',action='store_true')
    parser.add_argument('--wizard-names349',action='store_true')
    parser.add_argument('--release302-fixes',action='store_true')
    parser.add_argument('--hall-ramp',action='store_true')
    parser.add_argument('--hall-fractional-ramp',action='store_true')
    parser.add_argument('--hall-ramp-opt',choices=('-O3','-O2','-Os'),default='-O3')
    parser.add_argument('--eco-stock-reverb',action='store_true')
    parser.add_argument('--compression-candidates',type=int,default=1)
    parser.add_argument('--compression-history',action='store_true')
    parser.add_argument('--compression-window',type=int,default=1<<20)
    parser.add_argument('--compression-min-match',type=int,choices=(2,3,4),default=4)
    parser.add_argument('--compression-whole-image',action='store_true')
    parser.add_argument('--retain-owner',action='append',default=[],help='Diagnostic: conserver les sections dont le proprietaire contient ce texte')
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((args.reference/'BUILD.json').read_text());source=next(args.reference.glob('*.syx'))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['sha256']
    proof=json.loads((args.capture/'capture.json').read_text());assert proof['source']==meta['sha256']
    info,pkg,old,_=read(source);_,official,stock,ops=read(args.cycles)
    assert hashlib.sha256(args.cycles.read_bytes()).hexdigest()=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
    native=bytearray((args.capture/'native.bin').read_bytes());runtime=bytearray((args.capture/'runtime.bin').read_bytes());sram=bytearray((args.capture/'sram.bin').read_bytes())
    retirement=meta.get('clean_layout',{}).get('retirement')
    if args.retire_components:
        from rebuild300_policy import apply
        before=[bytes(x) for x in (native,runtime,sram)]
        retirement=apply(meta,[(BASE,native),(0x46700000,runtime),(0x80000000,sram)],proof,out)
        retained=[]
        for edit in retirement['edits']:
            if not any(token.casefold() in edit['owner'].casefold() for token in args.retain_owner):continue
            for base,raw,original in zip((BASE,0x46700000,0x80000000),(native,runtime,sram),before):
                at=edit['address']-base
                if 0<=at and at+edit['bytes']<=len(raw):
                    raw[at:at+edit['bytes']]=original[at:at+edit['bytes']];retained.append(edit);break
        retirement['edits']=[x for x in retirement['edits'] if x not in retained]
        retirement['diagnostic_retained']=retained
        retirement['changed_bytes']=sum(x['bytes'] for x in retirement['edits'])
    if args.wizard_lock_scope:
        from rebuild300_wizard import apply as wizard_apply
        meta['wizard_sample_lock_scope']=wizard_apply(meta,runtime,out)
    if args.retire_delegates:
        from rebuild300_delegates import apply as delegates_apply
        meta['retired_delegates']=delegates_apply(meta,[(BASE,native),(0x46700000,runtime),(0x80000000,sram)],out,args.retire_more_delegates)
    if args.wizard_sample_inherit:
        from rebuild300_wizard_source import apply as source_apply
        meta['wizard_sample_inherit']=source_apply(meta,native,runtime,out)
    if args.standalone_shared_entries:
        from rebuild300_shared_entries import apply as shared_apply
        meta['standalone_shared_entries']=shared_apply(meta,runtime,out,native,sram)
    if args.punch_work_gate:
        from rebuild300_punch_work import apply as punch_apply
        meta['punch_work_gate']=punch_apply(meta,runtime,out)
    if args.native_fx_unroll:
        from native_fx_unroll301 import apply as unroll_apply
        meta['native_fx_unroll']=unroll_apply(meta,native,runtime,stock,out)
    if args.fx_wake_recovery:
        from fx_wake303 import apply as wake_apply
        meta['fx_wake_recovery']=wake_apply(meta,native,runtime,stock,out)
    if args.diagnostic_midi:
        from diagnostic_midi303 import apply as diagnostic_apply
        meta['diagnostic_midi']=diagnostic_apply(meta,native,runtime,stock,out)
    if args.exact_zero_voices:
        from exact_zero_voice304 import apply as zero_apply
        meta['exact_zero_voices']=zero_apply(meta,runtime,sram,out)
    if args.eco_hall:
        from eco_hall305 import apply as eco_apply
        meta['eco_hall']=eco_apply(meta,runtime,out,args.eco_hall_sparse)
    if args.hall_merged_gain:
        from eco_hall305 import apply as hall_merge_apply
        meta['hall_merged_gain']=hall_merge_apply(meta,runtime,out,True,True)
    if args.delay_static:
        from delay_static307 import apply as delay_static_apply
        meta['delay_static']=delay_static_apply(meta,native,runtime,out)
    if args.filter_single_div:
        from filter_div307 import apply as filter_div_apply
        meta['filter_single_div']=filter_div_apply(meta,runtime,out)
    if args.chord_second_fast:
        from chord_second308 import apply as chord_second_apply
        meta['chord_second']=chord_second_apply(meta,native,runtime,sram,out)
    if args.filter_unroll:
        from filter_unroll308 import apply as filter_unroll_apply
        meta['filter_unroll']=filter_unroll_apply(meta,runtime,out)
    if args.fx_energy:
        from fx_energy309 import apply as energy_apply
        meta['fx_energy']=energy_apply(meta,native,runtime,sram,out)
    if args.silent_commit_guard:
        from silent_commit310 import apply as silent_apply
        meta['silent_commit_guard']=silent_apply(meta,native,runtime,sram,out)
    if args.quality_economy:
        from quality311 import apply as quality_apply
        meta['quality_economy']=quality_apply(meta,native,runtime,sram,out)
        for key,d in meta['quality_economy']['modules'].items():
            meta[key].update(code_bytes=d['code_bytes'],sha256=d['sha256'],symbols=d['symbols'],quality_unchanged=False)
    if args.idle_audit:
        from diagnostic_midi303 import apply as idle_audit_apply
        meta['diagnostic_midi']=idle_audit_apply(meta,native,runtime,sram,out,upgrade=True)
    if args.filter_half_rate:
        from filter_half312 import apply as half_apply
        meta['filter_half_rate']=half_apply(meta,runtime,out)
    if args.restore_filter_capture:
        from filter_restore315 import apply as restore_apply
        meta['filter_restore_48k']=restore_apply(meta,runtime,args.restore_filter_capture)
    if args.idle_scan_unroll:
        from fx_scan312 import apply as scan_apply
        meta['fx_scan_unroll']=scan_apply(meta,runtime,out)
        for key in ['code_bytes','symbols','sha256']:
            meta['fx_energy'][key]=meta['fx_scan_unroll'][key]
    if args.panic_stock:
        from panic_stock313 import apply as panic_apply
        meta['panic_stock']=panic_apply(meta,runtime,out)
        for key,field in [('code_bytes','scan_bytes'),('sha256','scan_sha256'),('symbols','scan_symbols')]:
            meta['fx_energy'][key]=meta['panic_stock'][field]
    if args.post_static:
        from post_static314 import apply as post_static_apply
        meta['post_static']=post_static_apply(meta,native,runtime,out)
    if args.post_dry_bypass:
        from post_static314 import apply as post_dry_apply
        meta['post_static']=post_dry_apply(meta,native,runtime,out,dry_bypass=True)
    if args.output_monitor_fast:
        from output_monitor316 import apply as output_apply
        meta['output_monitor_fast']=output_apply(meta,native,runtime,out)
    if args.upgrade_remote_data:
        from upgrade_key317 import apply as upgrade_key_apply
        meta['upgrade_remote_data']=upgrade_key_apply(meta,runtime,out)
    if args.deep_idle_wake or args.deep_idle_stop:
        from deep_idle329 import apply as deep_idle_apply
        meta['deep_idle_wake']=deep_idle_apply(meta,native,runtime,out,automatic_stop=args.deep_idle_stop)
    if args.remote_panel:
        from remote_panel318 import apply as remote_panel_apply
        meta['remote_panel']=remote_panel_apply(meta,native,runtime,out)
    if args.filter_full_cache:
        from filter_cache319 import apply as full_cache_apply
        meta['filter_single_div']=full_cache_apply(meta,runtime,out)
    if args.stage_profile:
        from stage_profile320 import apply as stage_profile_apply
        meta['stage_profile']=stage_profile_apply(meta,native,runtime,out)
    if args.without_stage_profile:
        assert not args.stage_profile
        if meta.get('stage_profile'):
            from stage_profile320 import remove as stage_profile_remove
            stage_profile_remove(meta,native,runtime)
            del meta['stage_profile']
        meta['detailed_profile_removed']=dict(complete_IRQ_accounting_retained=True,normal_DX_retained=True,overrun_and_cut_counters_retained=True)
    if args.hall_ramp:
        from hall_ramp322 import apply as hall_ramp_apply
        meta['hall_ramp']=hall_ramp_apply(meta,runtime,out,opt=args.hall_ramp_opt)
        meta['hall_merged_gain'].update(meta['hall_ramp'])
    if args.hall_fractional_ramp:
        from hall_ramp322 import apply as hall_fractional_apply
        meta['hall_fractional_ramp']=hall_fractional_apply(meta,runtime,out,opt='-O2',fractional=True)
        meta['hall_merged_gain'].update(meta['hall_fractional_ramp'])
    if args.sram_audio:
        from sram_audio337 import apply as sram_audio_apply
        meta['sram_audio']=sram_audio_apply(meta,native,runtime,sram,out,include_delay=args.sram_audio_delay,include_delay_filter=args.sram_delay_filter,full_delay=args.sram_full_delay,prefer_chord=args.sram_chord_priority)
    if args.chord_half_rate:
        from chord_half342 import apply as chord_half_apply
        meta['chord_half_rate']=chord_half_apply(meta,native,runtime,out)
    if args.voice_filter_unroll:
        from voice_filter343 import apply as voice_filter_apply
        meta['voice_filter_unroll']=voice_filter_apply(meta,native,sram,stock,out)
    if args.native_finish:
        from native_finish344 import apply as native_finish_apply
        meta['native_finish']=native_finish_apply(meta,native,runtime,sram,stock,out)
    if args.phase_loop or args.phase_sram:
        from phase_loop345 import apply as phase_loop_apply
        meta['phase_loop']=phase_loop_apply(meta,native,runtime,stock,out,sram=sram if args.phase_sram else None)
    if args.native_biquad:
        from native_biquad347 import apply as native_biquad_apply
        meta['native_biquad']=native_biquad_apply(meta,native,runtime,stock,out)
    if args.ui_fixes348:
        from ui_fixes348 import apply as ui_fixes_apply
        meta['ui_fixes348']=ui_fixes_apply(meta,native,runtime,out)
    if args.wizard_names349:
        from wizard_names349 import apply as names_apply
        meta['wizard_names349']=names_apply(meta,native,runtime,out)
    if args.release302_fixes:
        from release302_fixes import apply as release_apply
        release_apply(meta,native,runtime,sram,stock,out)
    if args.eco_stock_reverb:
        from eco_stock_reverb306 import apply as stock_eco_apply
        meta['eco_stock_reverb']=stock_eco_apply(native)
    # Conserver les donnees SRAM initiales de cette edition, jamais leur copie
    # effacee par clearBSS. Le reste du prefixe devient l'etat des hooks finaux.
    image=bytearray(old[:START]);boundary=0x4019b590-BASE;image[:boundary]=native[:boundary]
    image[0x400004b2-BASE:0x400004ba-BASE]=stock[0x400004b2-BASE:0x400004ba-BASE]
    # JSR de six octets + deux NOP : la reprise native est4000053a.
    image[0x40000530-BASE:0x4000053a-BASE]=b'\x4e\xb9'+struct.pack('>I',ENTRY)+b'\x4e\x71'*2
    image[0x4000053a-BASE:0x40000542-BASE]=stock[0x4000053a-BASE:0x40000542-BASE]
    if args.release!=meta['title_screen']['version']:
        from title204_assets import apply as title_apply
        def title_patch(at,expected,replacement,buffer):
            index=at-BASE;assert bytes(buffer[index:index+len(expected)])==expected
            buffer[index:index+len(replacement)]=replacement
        meta['title_screen']=title_apply(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),out,image,title_patch,args.release,lite=not meta['activity_masks']['full'],previous=meta['title_screen'])
    meta['release']=args.release
    spans=sparse(0x4019b590,native[boundary:])+sparse(0x46700000,runtime)+sparse(0x80000000,sram)
    table_size=4+12*len(spans);cursor=table_size;records=[];body=bytearray()
    for at,raw in spans:
        assert at%4==0 and len(raw)%4==0
        records.append((at,len(raw),cursor));body+=raw;cursor+=len(raw)
    payload=struct.pack('>I',len(records))+b''.join(struct.pack('>III',*r) for r in records)+body
    # Une seule compression, celle du conteneur : ne pas transformer le code
    # en donnees opaques incompressibles pour l'etage externe.
    packed=payload
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
    os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(tool,*v):return subprocess.check_output([cross+tool+'.exe',*map(str,v)],text=True)
    run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fno-tree-loop-distribute-patterns','-Wall','-Wextra','-Werror',f'-DRB_SOURCE={PACKED_SOURCE}','-DRB_RAW=1',f'-DRB_BYTES={len(payload)}', '-c',ROOT/'tools/machines/clean_build/loader.c','-o',out/'loader.o')
    (out/'loader.ld').write_text(f'SECTIONS {{ .text {RUN:#x} : {{ *(.text*) *(.rodata*) }} }}\n')
    run('ld','-T',out/'loader.ld','-e','rb_boot','-o',out/'loader.elf',out/'loader.o')
    run('objcopy','-O','binary',out/'loader.elf',out/'loader.bin')
    symbols={v[2]:int(v[0],16) for line in run('nm',out/'loader.elf').splitlines() if len(v:=line.split())==3}
    loader=(out/'loader.bin').read_bytes();loader+=bytes((-len(loader))&3);assert len(loader)<=3584
    asm=f'.text\n.globl rb_stage1\nrb_stage1:\n lea {STAGE_SOURCE:#x},%a0\n lea {RUN:#x},%a1\n move.l #{len(loader)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n move.l #0x000cc100,%d0\n movec %d0,%cacr\n nop\n jmp {symbols["rb_boot"]:#x}\n'
    (out/'stage.S').write_text(asm);run('gcc','-mcpu=54418','-c',out/'stage.S','-o',out/'stage.o');run('ld','-Ttext',hex(ENTRY),'-e','rb_stage1','-o',out/'stage.elf',out/'stage.o');run('objcopy','-O','binary',out/'stage.elf',out/'stage.bin')
    stub=(out/'stage.bin').read_bytes();assert len(stub)<=448
    extra=bytearray(4096);extra[:8]=MAGIC
    struct.pack_into('>10I',extra,8,1,ENTRY,RUN,STAGE_SOURCE,len(loader),PACKED_SOURCE,len(packed),len(payload),len(spans),symbols['rb_boot'])
    extra[64:64+len(stub)]=stub;extra[512:512+len(loader)]=loader
    image+=extra+packed
    dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START)
    assert 1<=args.compression_candidates<=64
    assert 4<=args.compression_window<=1<<24
    if args.compression_whole_image:
        writer=aplib._Writer()
        aplib_grow._tail(writer,bytes(image),0,1,args.compression_candidates,False,args.compression_window,args.compression_min_match)
        writer.end();writer.o[:4]=(len(writer.o)-8).to_bytes(4,'big');writer.o[4:8]=(sum(writer.o[8:])&0xffffffff).to_bytes(4,'big');stored=bytes(writer.o)
    else:stored=aplib_grow.repack_grow(bytes(image),ops,dirty,START,tail_candidates=args.compression_candidates,tail_history=args.compression_history,tail_window=args.compression_window,tail_minimum=args.compression_min_match)
    stored=compact_zero_runs(stored);stored,packing=pack(stored,preserve_short=True)
    assert aplib.depack(stored,bootstrap_gap=0x1ffc00)[0]==image
    plains=[]
    for section in official['sections']:
        try:plains.append(aplib.depack(official['blob'][section['off']:section['off']+section['size']])[0])
        except Exception:pass
    key=container.find_key(plains,official['blob'][:-32],official['blob'][-32:]);assert key
    rebuilt=container.rebuild(official,{3:stored},key);assert len(rebuilt)<=0x1c0000
    raw=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq'])
    (out/'Supermodel_3.00_Clean_Layout_Prototype.syx').write_bytes(raw)
    meta.update(sha256=hashlib.sha256(raw).hexdigest(),main_os_sha256=hashlib.sha256(image).hexdigest(),hardware_tested=False)
    meta['clean_layout']=dict(stage='packing prototype, ownership audit incomplete',magic=MAGIC.decode(),entry=ENTRY,runner=RUN,runner_entry=symbols['rb_boot'],runner_bytes=len(loader),payload_codec='outer container only',payload_bytes=len(payload),packed_payload_bytes=len(packed),segments=[dict(address=a,bytes=n,offset=o) for a,n,o in records],reference_sha256=proof['source'],historical_loaders_executed=False,source_rebuild_complete=False,packing=packing)
    if retirement:meta['clean_layout']['retirement']=retirement
    meta['clean_layout']['compression_search']=dict(candidates=args.compression_candidates,history=args.compression_history,window=args.compression_window,minimum_match=args.compression_min_match,whole_image=args.compression_whole_image)
    (out/'BUILD.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('PROTOTYPE',len(raw),'SYX bytes; old',source.stat().st_size,'; payload',len(payload),'->',len(packed),'; boot literal padding',packing['added_literal_bytes'],flush=True)


if __name__=='__main__':main()
