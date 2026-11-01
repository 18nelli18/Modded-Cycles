"""Comparaison privee2.94 : deuxieme operateur FM, une seule modulation utile, politique2.93."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x4691e400;BSS=0x4691ef00
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='9028789da5ca04f29a251a540c1fc83c52d1831d44cd4f2c74db3be830de2762');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
am=m['activity_masks'];
if am['code']>=0x4691c400:CODE=0x46928000;BSS=0x4692f000
ps=m['per_track_fx']['symbols'];cal=m['control_all_latch'];assert cal['code']+cal['code_bytes']<=CODE<BSS and cal['bss_end']<=0x46920000
aliases={k:ps[k] for k in ['gb_irq_active','gb_irq_t0','gb_budget_t0','mf_old_audio_end']};aliases.update({k:ps[k] for k in ['mf_old_sum6','mf_old_sum7','lt_native_zero','lt_native_one']});aliases.update(sg_resume6=ps['mf_old_sum6']+8,sg_resume7=ps['mf_old_sum7']+8);aliases['ig_old_boot']=cal['boot_target'];aliases.update(dt_enabled=m['dx_symbols']['dx_enabled'],dt_api=m['fx_menu']['symbols']['dx_beat_api'])
end=int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE;compressed=image[START:end]
runtime=aplib.depack(struct.pack('>II',len(compressed),sum(compressed)&0xffffffff)+compressed)[0]
anchor=bytes.fromhex('2800ef8c41f980001858');off=runtime.find(anchor);assert runtime.count(anchor)==1 and 0x5858<=off<0x7878
key_address=0x8000cac0+off-0x5858;body=runtime[off:off+160];gain_candidates=[int.from_bytes(body[i+2:i+6],'big') for i in range(0,154,2) if body[i:i+2]==b'\x41\xf9'];assert gain_candidates[0]==0x80001858;gain_list=gain_candidates[1]
free_offset=0x5858+0x8000ea48-0x8000cac0;assert not any(runtime[free_offset:free_offset+152])
(O/'key.ld').write_text('SECTIONS { .text 0x8000ea48 : { *(.text*) } }\nGOV_GAINS = '+hex(gain_list)+';\n')
run('gcc','-mcpu=54418','-c',R/'tools/machines/gov/key-fast.S','-o',O/'key.o');run('ld','-T',O/'key.ld','-e','kg_key','-o',O/'key.elf',O/'key.o');run('objcopy','-O','binary',O/'key.elf',O/'key.bin');key_code=(O/'key.bin').read_bytes();assert len(key_code)<=152;key_blob=key_code+bytes((-len(key_code))&3)
aliases['kg_native_entry']=0x8000ea48
asm=(R/'tools/machines/track_fx/irq-complete.S').read_text(encoding='utf-8').replace('jsr mf_old_audio_end','jsr dt_audio_end');late=[]
# Les deux instructions deplacees sont des lectures absolues du timer, sans PC relatif.
for name,label,expected in [('gb_audio_end','ig_previous_audio','2039fc07000c'),('gb_irq_end','ig_previous_irq','2f39fc07000c')]:
 at=ps[name];oldend=int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE;offset=oldend+at-0x467ab360;raw=bytes(image[offset:offset+6]);assert raw.hex()==expected
 asm+=f'.globl {label}\n{label}:\n.byte '+','.join(map(str,raw))+f'\n jmp {at+6:#x}\n';late.append((at,'ig_audio_end' if name=='gb_audio_end' else 'ig_irq_end',6))
late.append((key_address,'kg_native_entry',6))
trig_offset=0x5858+0x8000e8f0-0x8000cac0
assert runtime[trig_offset:trig_offset+2].hex()=='4ef9'
aliases['qt_old_trig']=int.from_bytes(runtime[trig_offset+2:trig_offset+6],'big')
assert runtime[0x8000734c-0x80001c5c:0x8000734c-0x80001c5c+6].hex()=='263c00002000'
late.extend([(0x8000e8f0,'qt_trig',6),(0x8000734c,'qt_scan_gate',6),(ps['native_sum'],'ns_sum',6)])
for n,expected in [(6,'4fefffe048d70cfc'),(7,'4fefffd848d73cfc')]:
 address=ps['mf_old_sum'+str(n)];offset=end+address-0x467ab360
 assert bytes(image[offset:offset+8]).hex()==expected
 late.append((address,'sg_sum'+str(n),8))
govern_offset=0x5858+0x8000e794-0x8000cac0
assert runtime[govern_offset:govern_offset+8].hex()=='4fefffc048d73cfc'
late.append((0x8000e794,'ph_govern',8))
finish_at=ps['gb_finish'];finish_offset=end+finish_at-0x467ab360
finish_prefix=bytes(image[finish_offset:finish_offset+6]);assert finish_prefix==b'\x20\x79'+struct.pack('>I',ps['gb_irq_t0'])
late.append((finish_at,'fg_finish',6));aliases.update(fg_base=ps['gb_irq_active'],fg_dxbase=ps['gb_enabled'])
fields={'FG_T0':ps['gb_irq_t0']-ps['gb_irq_active'],'FG_BUDGET':ps['gb_budget_t0']-ps['gb_irq_active'],'FG_TOTAL':ps['gb_last_total']-ps['gb_irq_active'],'FG_TAIL':ps['gb_last_tail']-ps['gb_irq_active'],'FG_PEAK':ps['gb_peak']-ps['gb_enabled'],'FG_OVER':ps['gb_over']-ps['gb_enabled'],'FG_BLOCKS':ps['gb_blocks']-ps['gb_enabled'],'FG_SUM':ps['gb_sum']-ps['gb_enabled']}
assert all(-32768<=x<32768 for x in fields.values());(O/'finish-offsets.inc').write_text(''.join(f'.equ {name}, {value}\n' for name,value in fields.items()))
dry_at=ps['dry_osc'];dry_offset=end+dry_at-0x467ab360;dry_body=bytes(image[dry_offset:dry_offset+512]);dry_marker=bytes.fromhex('246f0054226f00587020');native_marker=stock[0x400a82cc-BASE:0x400a82d4-BASE]+bytes.fromhex('4ef9400a82d4')
assert dry_body.count(dry_marker)==dry_body.count(native_marker)==1
aliases.update(om_dry=dry_at+dry_body.index(dry_marker),om_native=dry_at+dry_body.index(native_marker))
assert bytes(image[0x400a82cc-BASE:0x400a82d2-BASE])==b'\x4e\xf9'+struct.pack('>I',dry_at)
late.append((0x400a82cc,'om_osc',6))
# Initialiseur de la charge utile : ne remplace pas une preference valide.
f=m['activity_masks'];default_at=f['loader']+512+f['symbols']['mb_silent']-f['code']-BASE
assert bytes(image[default_at:default_at+4])==bytes.fromhex('00000001')
image[default_at:default_at+4]=bytes(4)

# Ne contourne que le test quiet des moteurs natifs ; stolen reste teste avant ce detour.
qoff=0x5858+0x8000e91e-0x8000cac0
assert runtime[qoff:qoff+6].hex()=='73b1085e7440'
late.append((0x8000e91e,'qt_cached_gate',6))
asm+='\nqt_gate:\n moveq #5,%d1\n cmp.l 16(%sp),%d1\n bcs.s .Lqt_added\n clr.b 0x5e(%a1,%d0.l)\n jmp 0x8000e930\n.Lqt_added:\n mvz.b 0x5e(%a1,%d0.l),%d1\n moveq #64,%d2\n jmp 0x8000e924\n'

asm+='\n.text\n.balign 4\n.globl kg_source\nkg_source:\n.byte '+','.join(map(str,key_blob))+'\n'
asm+='ig_install:\n lea -16(%sp),%sp\n movem.l %d0-%d1/%a0-%a1,(%sp)\n'
asm+=f' lea kg_source,%a0\n lea 0x8000ea48,%a1\n move.l #{len(key_blob)//4},%d0\n.Lcopy_key: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s .Lcopy_key\n'
for at,fn,n in late:
 asm+=f' lea {at:#x},%a1\n move.w #0x4ef9,(%a1)+\n move.l #{fn},(%a1)\n'
 if n==8:asm+=' move.w #0x4e71,4(%a1)\n'
asm+=' jsr dt_init\n movem.l (%sp),%d0-%d1/%a0-%a1\n lea 16(%sp),%sp\n jmp ig_old_boot\n'
(O/'bridge.S').write_text(asm,encoding='utf-8')
(O/'module.ld').write_text('SECTIONS { .text '+hex(CODE)+' : { *(.text*) *(.rodata*) *(.data*) } .bss '+hex(BSS)+' (NOLOAD) : { *(.bss*) } ig_end = .; }\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
run('gcc','-mcpu=54418','-c',O/'bridge.S','-o',O/'bridge.o');run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-c',R/'tools/machines/track_fx/track5-cause-fast.c','-o',O/'trace.o');run('gcc','-mcpu=54418','-c',R/'tools/machines/track_fx/stock-voice-admin.S','-o',O/'admin.o');run('gcc','-mcpu=54418','-c',R/'tools/machines/track_fx/mixer-dispatch.S','-o',O/'mixer.o');run('gcc','-mcpu=54418','-c',R/'tools/machines/track_fx/static-gain-mix.S','-o',O/'static-mix.o');run('gcc','-mcpu=54418','-c',R/'tools/machines/track_fx/deadline-tight.S','-o',O/'deadline.o');run('gcc','-mcpu=54418','-I',O,'-c',R/'tools/machines/track_fx/finish-fast.S','-o',O/'finish.o');run('gcc','-mcpu=54418','-c',R/'tools/machines/track_fx/one-mod-second.S','-o',O/'osc-second.o');run('ld','-T',O/'module.ld','-e','ig_install','-o',O/'module.elf',O/'bridge.o',O/'trace.o',O/'admin.o',O/'mixer.o',O/'static-mix.o',O/'deadline.o',O/'finish.o',O/'osc-second.o');run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=BSS and s['ig_end']<=BSS+0x100
relay_patch=cal['boot_relay_patch'];assert image[relay_patch-BASE:relay_patch-BASE+4]==struct.pack('>I',cal['boot_target']);struct.pack_into('>I',image,relay_patch-BASE,s['ig_install'])
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(s['ig_end']-BSS+3)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
(O/'load.S').write_text(load);run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','cal_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob
from title204_assets import apply
# Identifiant experimental distinct ; aucun push/flasher modifie.
def patch(at,old,new,buf):assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
m['title_screen']=apply(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,patch,'2.94',lite=not am['full'],previous=m['title_screen'])
# Tokens de compression officiels, comme les generateurs prives existants.
stockops=read(a.cycles)[3];dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),stockops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
plains=[]
for sec in pkg['sections']:
 try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
 except Exception:pass
key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_2.94_Single_Modulator_Experimental.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
m['complete_irq_accounting']=dict(code=CODE,code_bytes=len(blob),symbols=s,loader=loader,previous_loader=oldentry,boot_target=s['ig_install'],late_hooks=[dict(at=at,target=s[fn],bytes=n) for at,fn,n in late],source_sha256=sha(a.source.read_bytes()),thresholds_unchanged=True,hardware_tested=False)
m['governor_key_optimization']=dict(original_entry=key_address,original_prefix=runtime[off:off+6].hex(),gain_list=gain_list,target=0x8000ea48,code_bytes=len(key_code),sha256=sha(key_code),free_bytes=152,decision_policy_unchanged=True,all_features_retained=True,hardware_tested=False)
m['stock_tail_parity']=dict(gate=0x8000e91e,helper=s['qt_gate'],stock_engines=list(range(6)),forced_fades_retained=True,native_idle_retained=True,hardware_tested=False)
m['track_cut_trace']=dict(symbols=s,popup='V counts for tracks1 through6, capped99 per capture; replaces A/P/O/N only in this private diagnostic',hardware_tested=False)
m['machine_browse_default']=dict(value='Stk',saved_preference_retained=True,initializer_at=default_at+BASE)
m['stock_voice_admin']=dict(symbols=s,quiet_scan_bypassed_for_native_only=True,overload_policy_unchanged=True,hardware_tested=False)
m['mixer_dispatch']=dict(symbols=s,hook=ps['native_sum'],target=s['ns_sum'],hardware_tested=False)
m['static_gain_mixer']=dict(symbols=s,code=s['sg_sum6'],code_bytes=s['sg_mix_end']-s['sg_sum6'],sha256=sha(blob[s['sg_sum6']-CODE:s['sg_mix_end']-CODE]),gain_ramp_fallback=True,delta_output_overlap_fallback=True,hardware_tested=False)
m['deadline_headroom']=dict(hook=0x8000e794,target=s['ph_govern'],sustained_threshold_q=220,deadline_q=256,reserve_q=1,relief_threshold_q=255,original_prefix=runtime[govern_offset:govern_offset+8].hex(),sustained_relief_retained=True,current_overrun_response_retained=True,hardware_tested=False)
m['complete_irq_accounting'].update(thresholds_unchanged=False,load_accounting_unchanged=True)
m['stock_voice_admin'].update(overload_policy_unchanged=False)
m['governor_key_optimization'].update(decision_policy_unchanged=False,ranking_unchanged=True)
m['track_cut_trace']['popup']='T5 S sustained percent / L current-block percent, nearest integer; last track5 forced fade only'
m['track5_cut_cause']=dict(symbols=s,policy_same_as=None,hardware_tested=False)
m['irq_finish_fast']=dict(hook=finish_at,target=s['fg_finish'],original_prefix=finish_prefix.hex(),statistics_unchanged=True,hardware_tested=False)
m['native_second_mod']=dict(symbols=s,target=s['om_osc'],code=s['om_osc'],code_bytes=s['om_second_end']-s['om_osc'],sha256=sha(blob[s['om_osc']-CODE:s['om_second_end']-CODE]),first_operator_unchanged=True,policy_same_as='2.93',hardware_tested=False)
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT complete IRQ accounting',len(blob),'code bytes',sha(result),flush=True)
