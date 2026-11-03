"""Reveil par signal : remplacer idle_present dans l ancien HALL chaud mort."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
def apply(meta,native,runtime,sram,out):
    base=0x46700000;retired=meta['audio_headroom']['hall'];code=retired['code'];capacity=meta['audio_headroom']['hall_code_bytes']
    assert meta['hall_merged_gain']['code']!=code
    assert runtime[meta['fx_menu']['symbols']['fx_hall']-base:meta['fx_menu']['symbols']['fx_hall']-base+6]==b'\x4e\xf9'+struct.pack('>I',meta['hall_merged_gain']['symbols']['fx_hall'])
    needle=struct.pack('>I',code);assert needle not in runtime and needle not in native and needle not in sram
    before=bytes(runtime[code-base:code-base+capacity]);assert any(before)
    ps=meta['per_track_fx']['symbols'];fs=meta['fx_menu']['symbols']
    aliases=dict(ei_started=ps['idle_started'],ei_woken=ps['idle_woken'],ei_rev=fs['ch_mode'],ei_del=fs['cr_mode'],ei_ractive=fs['active'],ei_dactive=fs['nd_active'],ei_side=ps['mf_side'],ei_side_on=ps['mf_side_on'])
    out=Path(out);out.mkdir(parents=True,exist_ok=True);cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    (out/'fx-energy.ld').write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) *(.rodata*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
    run('gcc','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/track_fx/fx-energy309.c','-o',out/'fx-energy.o');run('ld','-T',out/'fx-energy.ld','-e','ei_present','-o',out/'fx-energy.elf',out/'fx-energy.o');run('objcopy','-O','binary',out/'fx-energy.elf',out/'fx-energy.bin')
    blob=(out/'fx-energy.bin').read_bytes();assert len(blob)<=capacity
    sy={v[2]:int(v[0],16) for line in run('nm',out/'fx-energy.elf').splitlines() if len(v:=line.split())==3}
    at=ps['idle_present'];old=bytes(runtime[at-base:at-base+6]);assert old[:2]==bytes.fromhex('4fef')
    new=b'\x4e\xf9'+struct.pack('>I',sy['ei_present']);runtime[at-base:at-base+6]=new;runtime[code-base:code-base+capacity]=blob+bytes(capacity-len(blob))
    return dict(code=code,code_bytes=len(blob),reclaimed_bytes=capacity,retired_sha256=hashlib.sha256(before).hexdigest(),symbols=sy,aliases=aliases,patches=[dict(at=at,old=old.hex(),new=new.hex())],sha256=hashlib.sha256(blob).hexdigest(),new_state_bytes=0,active_transport_policy_unchanged=True,custom_awake_tail_latch_unchanged=True,native_tail_detector_unchanged=True,hardware_tested=False)
