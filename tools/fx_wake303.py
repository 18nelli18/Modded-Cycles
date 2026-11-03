"""Veille des FX deja vides : liberer le latch au panic, garder tout signal actif."""
from pathlib import Path
import hashlib,os,struct,subprocess

CODE=0x46701000
ROOT=Path(__file__).resolve().parents[1]
def apply(meta,native,runtime,stock,out):
    sy=meta['per_track_fx']['symbols'];fx=meta['fx_menu'];fs=fx['symbols'];base=0x46700000;offset=CODE-base
    assert meta.get('clean_layout',{}).get('historical_loaders_executed') is False
    assert any(x['kind']=='remove' and x['address']<=CODE and CODE+4096<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
    assert not any(runtime[offset:offset+4096])
    targets={k:fs[k] for k in ['fx_ps1','fx_room','fx_hall','fx_ring','fx_gated','ch_chorus'] if k in fs}
    targets['pots_process']=sy['pots_process']
    asm='.text\n.balign 4\n.globl fw_panic_release\nfw_panic_release:\njsr '+hex(sy['lt_panic'])+'\nclr.l '+hex(sy['idle_woken'])+'\nclr.l '+hex(sy['idle_started'])+'\nrts\n'
    for name,at in targets.items():
        label='fw_'+name
        asm+='\n.balign 4\n.globl '+label+'\n'+label+':\ntst.l 0x401b72ec\nbne.s .Lcheck_'+name+'\njmp '+hex(at)+'\n.Lcheck_'+name+':\nmovea.l 8(%sp),%a0\nmoveq #15,%d0\n.Linput_'+name+':\nmove.l (%a0)+,%d1\nor.l (%a0)+,%d1\nor.l (%a0)+,%d1\nor.l (%a0)+,%d1\nbne.s .Lwake_'+name+'\nsubq.l #1,%d0\nbpl.s .Linput_'+name+'\nmovea.l 4(%sp),%a0\nmoveq #15,%d0\n.Lzero_'+name+':\n.rept 4\nclr.l (%a0)+\n.endr\nsubq.l #1,%d0\nbpl.s .Lzero_'+name+'\nrts\n.Lwake_'+name+':\njmp '+hex(at)+'\n'
    out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'fx-wake.S').write_text(asm)
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*args):return subprocess.check_output([cross+t+'.exe',*map(str,args)],text=True)
    run('gcc','-mcpu=54418','-c',out/'fx-wake.S','-o',out/'fx-wake.o');run('ld','-Ttext',hex(CODE),'-e','fw_panic_release','-o',out/'fx-wake.elf',out/'fx-wake.o');run('objcopy','-O','binary',out/'fx-wake.elf',out/'fx-wake.bin')
    symbols={v[2]:int(v[0],16) for line in run('nm',out/'fx-wake.elf').splitlines() if len(v:=line.split())==3};blob=(out/'fx-wake.bin').read_bytes();assert len(blob)<4096
    patches=[]
    def redirect(lo,hi,target,replacement,required=True):
        old=b'\x4e\xb9'+struct.pack('>I',target);found=[]
        for at in range(lo,hi-5,2):
            if runtime[at-base:at-base+6]==old:found.append(at)
        if required:assert found,(hex(lo),hex(target))
        for at in found:
            new=b'\x4e\xb9'+struct.pack('>I',replacement);runtime[at-base:at-base+6]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
    redirect(sy['mf_fx_begin'],sy['mf_fx_begin']+96,sy['lt_panic'],symbols['fw_panic_release'])
    for name,target in targets.items():
        lo,hi=(sy['pots_slot_delay'],sy['pots_process']) if name=='pots_process' else (fx['code'],fx['code']+fx['code_bytes'])
        redirect(lo,hi,target,symbols['fw_'+name])
    runtime[offset:offset+len(blob)]=blob
    return dict(code=CODE,code_bytes=len(blob),symbols=symbols,patches=patches,sha256=hashlib.sha256(blob).hexdigest(),new_state_bytes=0,nonzero_input_always_processed=True,awake_tails_always_processed=True,panic_releases_wake_latch=True,stock_native_kernels_unchanged=True,hardware_tested=False)
