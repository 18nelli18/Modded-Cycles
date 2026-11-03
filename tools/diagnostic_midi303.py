"""Ajouter une lecture DX privee dans les seules requetes/reponses RPC version."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1];CODE=0x46701800;BSS=0x46701f00
def apply(meta,native,runtime,stock,out,upgrade=False):
    ps=meta['per_track_fx']['symbols'];fs=meta['fx_menu']['symbols'];am=meta['activity_masks']['symbols'];ex=meta['transfer300']['symbols'];base=0x46700000
    prior=meta.get('diagnostic_midi') if upgrade else None
    if prior:
        assert prior['code']==CODE and hashlib.sha256(runtime[CODE-base:CODE-base+prior['code_bytes']]).hexdigest()==prior['sha256']
        assert not any(runtime[CODE-base+prior['code_bytes']:BSS-base])
    else:assert not any(runtime[CODE-base:BSS-base+16])
    aliases=dict(dx_old_request=ex['ex_request'],dx_old_send=ex['ex_send'],dx_now=ps['gb_last_total'],dx_peak=ps['gb_peak'],dx_over=ps['gb_over'],dx_cuts=meta['dx_symbols']['dx_new'],dx_lfo=am['li_active_tracks'],dx_punch=am['pp_custom_mask'],dx_light=ps['lt_active'],dx_woken=ps['idle_woken'],dx_started=ps['idle_started'],dx_mode=ps['mf_mode'],dx_enabled=meta['dx_symbols']['dx_enabled'],dx_rev=fs['ch_mode'],dx_del=fs['cr_mode'],dx_active_rev=fs['active'],dx_active_del=fs['nd_active'],dx_requested=ps['mf_requested'])
    if upgrade:
        # La porte SRAM utilise GB46732000 ; gb_mask est une copie historique.
        if stock:assert stock[0xe8a6:0xe8ac]==bytes.fromhex('43f946732000')
        aliases.update(dx_quiet=0x4673205e,dx_engines=meta['exact_zero_voices']['symbols']['qt_engines'])
    out=Path(out);out.mkdir(parents=True,exist_ok=True);cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    ld=out/'diagnostic-midi.ld';ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) *(.data*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) }} dx_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
    run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DDX_IDLE_AUDIT'] if upgrade else []),'-c',ROOT/'tools/machines/track_fx/diagnostic-midi303.c','-o',out/'diagnostic-midi.o');run('ld','-T',ld,'-o',out/'diagnostic-midi.elf',out/'diagnostic-midi.o');run('objcopy','-O','binary',out/'diagnostic-midi.elf',out/'diagnostic-midi.bin')
    symbols={v[2]:int(v[0],16) for line in run('nm',out/'diagnostic-midi.elf').splitlines() if len(v:=line.split())==3};blob=(out/'diagnostic-midi.bin').read_bytes();assert CODE+len(blob)<=BSS and symbols['dx_end']<=BSS+16
    patches=[]
    for caller,oldfn,newfn in [('ex_type','ex_request','dx_request'),('ex_output','ex_send','dx_send')]:
        at=ex[caller];old=b'\x4e\xb9'+struct.pack('>I',prior['symbols'][newfn] if prior else ex[oldfn]);chunk=bytes(runtime[at-base:at-base+64]);assert chunk.count(old)==1
        site=at+chunk.index(old);new=b'\x4e\xb9'+struct.pack('>I',symbols[newfn]);runtime[site-base:site-base+6]=new;patches.append(dict(at=site,old=old.hex(),new=new.hex()))
    runtime[CODE-base:BSS-base]=blob+bytes(BSS-CODE-len(blob))
    return dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_bytes=symbols['dx_end']-BSS,symbols=symbols,aliases=aliases,patches=patches,sha256=hashlib.sha256(blob).hexdigest(),read_only=True,audio_hooks=False,reply_size_unchanged=True,private_requests=['SMDX303!','SMCT303!','SMFX303!']+(['SMVI303!']+['SME%d303!'%t for t in range(6)]+['SMA%d303!'%t for t in range(6)] if upgrade else []),hardware_tested=False)
