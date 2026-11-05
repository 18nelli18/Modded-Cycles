"""Extension privee GOV INV et effets master seuls, banques FX conservees."""
from pathlib import Path
import hashlib
import os
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE,CODE,END=0x46700000,0x467a5000,0x467a5800
CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'

def apply(meta,native,runtime,sram,out,hide_fx=False):
    assert meta.get('fx_mst_save379') and not meta.get('gov_inv_master380')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not any(runtime[CODE-BASE:END-BASE])
    assert any(e['kind']=='remove' and e['address']<=CODE and END<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
    for profile in meta.values():
        if not isinstance(profile,dict):continue
        for kind in ('code','bss'):
            at,size=profile.get(kind),profile.get(kind+'_bytes',0)
            if isinstance(at,int) and isinstance(size,int) and size:assert END<=at or at+size<=CODE
    gp=meta['gov_policy372'];gs=gp['symbols'];mf=meta['per_track_fx']['symbols']
    aliases={**gp['aliases'],**gs}
    aliases.update(mo_mode=mf['mf_mode'],mo_loaded=mf['mode_loaded'],mo_dirty=mf['mode_dirty'],mo_tree_delegate=mf['mf_old_tree_edit'])
    text=(ROOT/'tools/machines/track_fx/gov-policy372.c').read_text()
    def function(name):
        start=text.index(name+'(');start=text.rfind('\n',0,start)+1
        brace=text.index('{',start);level=1;end=brace+1
        while level:
            level+=(text[end]=='{')-(text[end]=='}');end+=1
        return text[start:end]+'\n'
    c=out/'gov.c'
    c.write_text('typedef unsigned int u32;typedef int s32;typedef unsigned char u8;\n'
        '#define N(a) ((u32(*)())(a))\n'
        'extern volatile u32 menu,row,gc_level,gc_tree_cursor,gc_page,sx_submenu,du_page,mq_page;\n'
        'extern volatile u32 gp_mode;extern u32 edit,dirty,changed,loaded;\n'
        'extern u32 gp_edit(void),gp_old_edit(void),gp_old_encoder(const u32*),gc_input_quiet(void);\n'
        f'#define GP_ROW {gp["global_row"]}\n'+
        (f'#define GP_MASTER_NO_ROW\n#define GP_AFTER_FX_ROW {12 if meta["activity_masks"]["full"] else 13}\n' if hide_fx else '')+
        ''.join(function(n) for n in ('global','redraw','gp_set','gp_value','gp_encoder','gp_service')))
    from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
    cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
    tramp='.text\n';master_hooks=[]
    for name,target,oldname in [('mf_frame','mo_frame','mo_old_frame'),('mf_gc_key','mo_key','mo_old_key')]:
        at=mf[name];raw=bytes(runtime[at-BASE:at-BASE+24]);n=0
        for ins in cs.disasm(raw,at):
            assert not ins.mnemonic.startswith(('b','j')) and 'pc' not in ins.op_str
            n+=ins.size
            if n>=6:break
        assert n>=6
        tramp+=f'.globl {oldname}\n{oldname}:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n'
        master_hooks.append((at,target,n))
    (out/'old.S').write_text(tramp)
    os.environ['PATH']=str(Path(CROSS).parent)+os.pathsep+os.environ['PATH']
    def run(tool,*args):return subprocess.check_output([CROSS+tool+'.exe',*map(str,args)],text=True)
    objects=[]
    for src in (c,ROOT/'tools/machines/track_fx/master-only380.c',out/'old.S'):
        obj=out/(src.name+'.o');objects.append(obj)
        run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',src,'-o',obj)
    needed=set()
    for obj in objects:needed.update(line.split()[-1] for line in run('nm','-u',obj).splitlines())
    ld=out/'inv-master.ld';ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss (NOLOAD) : {{ *(.bss*) *(COMMON) }} }}\n'+''.join(f'{k} = {aliases[k]:#x};\n' for k in needed if k in aliases and k not in ('gp_set',)))
    elf=out/'inv-master.elf';binary=out/'inv-master.bin'
    run('ld','-T',ld,'-o',elf,*objects);run('objcopy','-O','binary','-j','.text',elf,binary)
    raw=binary.read_bytes();assert CODE+len(raw)<=END
    symbols={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3}
    patches=[]
    def patch(buf,base,at,data):
        offset=at-base;assert 0<=offset<=len(buf)-len(data)
        old=bytes(buf[offset:offset+len(data)]);buf[offset:offset+len(data)]=data
        patches.append(dict(region='sram' if base==0x80000000 else 'runtime',at=at,old=old.hex(),new=data.hex()))
    patch(runtime,BASE,CODE,raw)
    for name in ('gp_set','gp_value','gp_service'):
        patch(runtime,BASE,gs[name],b'\x4e\xf9'+struct.pack('>I',symbols[name]))
    # Garder la chaine Swap -> GOV : remplacer le trampoline d'entree de Swap.
    ts=meta['track_swap377']['symbols'];at=ts['ts_old_encoder']
    assert runtime[gs['gp_encoder']-BASE:gs['gp_encoder']-BASE+2]==b'\x4e\xf9'
    patch(runtime,BASE,at,b'\x4e\xf9'+struct.pack('>I',symbols['gp_encoder']))
    for at,target,n in master_hooks:
        patch(runtime,BASE,at,b'\x4e\xf9'+struct.pack('>I',symbols[target])+b'\x4e\x71'*((n-6)//2))
    for old,target in [('mf_mode_set','mo_set'),('mf_tree_edit','mo_edit')]:
        patch(runtime,BASE,mf[old],b'\x4e\xf9'+struct.pack('>I',symbols[target]))
    g=meta['governor_key_optimization'];stub=g['target']+g['code_bytes']
    old=b'\x4a\xb9'+struct.pack('>I',gs['gp_mode'])+b'\x67\x04\x24\x00\x4e\x75\x4e\xf9'+struct.pack('>I',g['target'])
    assert sram[stub-0x80000000:stub-0x80000000+18]==old
    rankld=out/'rank.ld';rankld.write_text(f'SECTIONS {{ .text {stub:#x} : {{ *(.text*) }} }}\ngi_mode = {gs["gp_mode"]:#x};\ngi_lod = {g["target"]:#x};\n')
    rankobj,rankelf,rankbin=[out/('rank.'+ext) for ext in ('o','elf','bin')]
    run('gcc','-mcpu=54418','-c',ROOT/'tools/machines/track_fx/gov-inv380.S','-o',rankobj)
    run('ld','-T',rankld,'-o',rankelf,rankobj);run('objcopy','-O','binary',rankelf,rankbin)
    rank=rankbin.read_bytes();assert len(rank)<=g['free_bytes']-g['code_bytes']
    rank_symbols={v[2]:int(v[0],16) for line in run('nm',rankelf).splitlines() if len(v:=line.split())==3}
    rank_entry=rank_symbols['gi_rank']
    assert not any(sram[stub-0x80000000+18:stub-0x80000000+len(rank)])
    patch(sram,0x80000000,stub,rank)
    assert sram[g['original_entry']-0x80000000:g['original_entry']-0x80000000+6]==b'\x4e\xf9'+struct.pack('>I',stub)
    patch(sram,0x80000000,g['original_entry'],b'\x4e\xf9'+struct.pack('>I',rank_entry))
    gp.update(modes=['Lod','Trk','INV'],master_FX_only=True)
    return dict(code=CODE,code_bytes=len(raw),end=END,symbols=symbols,patches=patches,
        rank_entry=rank_entry,rank_storage=stub,rank_bytes=len(rank),rank_order=[6,5,4,3,2,1],
        master_FX_only=True,FX_saved_per_pattern=True,FX_selector_read_only='MST',
        thresholds_unchanged=True,eligibility_unchanged=True,fades_unchanged=True,
        code_sha256=hashlib.sha256(raw).hexdigest(),hardware_tested=False)
