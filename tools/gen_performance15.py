# SPDX-License-Identifier: MIT
"""Compile le mode Performance autonome depuis l'OS 1.13 officiel (notes/58).

Contribution experimentale, volontairement absente du catalogue du flasheur.
  python3 tools/gen_performance15.py --cycles firmware/model-cycles_OS1.13.syx --check
"""
from pathlib import Path
import argparse,hashlib,json,re,struct,subprocess,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'tools/machines/performance15'
sys.path.insert(0,str(SRC))
from performance_registry import load as load_registry
import build as native_build
from mtlib import aplib,container
from mtlib.syx import unwrap,wrap,BYTES_PER_MSG
CROSS=next((c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'gcc')),'m68k-linux-gnu-')
BASE=0x40000400
RUNTIME=0x42339000
STOCK_SHA='cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98'
SOURCE_SHA='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
def require(condition,message):
    if not condition:raise SystemExit(message)

def run(*args):
    subprocess.run([str(a) for a in args],cwd=ROOT,check=True)
def compile_mode(cycles):
    SOURCE=Path(cycles)
    registry=load_registry();out=ROOT/'build/performance15';out.mkdir(parents=True,exist_ok=True)
    (out/'performance_registry.generated.h').write_text(registry.header())
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA,'OS officiel 1.13 requis (SHA-256 du SysEx)')
    stream,_=unwrap(SOURCE.read_bytes());info=container.parse(stream)
    section=next(s for s in info['sections'] if s['id']==3)
    stock=aplib.depack(info['blob'][section['off']:section['off']+section['size']])[0]
    require(hashlib.sha256(stock).hexdigest()==STOCK_SHA,'MAIN OS officiel 1.13 requis')
    replay=['.text']
    hooks=[
      (0x400060fe,'4feffff048d70c0c','per_root_key','per_root_key_stock'),
      (0x4001040e,'4e56ffc4222e000c','per_temp_save','per_temp_save_stock'),
      (0x400107d8,'4e56ffc4222e000c','per_temp_reload','per_temp_reload_stock'),
      (0x4001134e,'4e56ff9c48d73cfc','per_project_ctor','per_project_ctor_stock'),
      (0x4005b2ae,'4fefffe448d77c0c','per_encode','per_encode_stock'),
      (0x4005d080,'4fefffdc48d77c3c','per_decode','per_decode_stock'),
      (0x40061374,'4fefffec48d73c04','per_clear_kit','per_clear_kit_stock'),
      (0x40055c38,'2f0a2f02246f000c','per_commit','per_commit_stock'),
      (0x400583ba,'202f0004222f0008','per_track_level','per_track_level_stock'),
      (0x400595a8,'4fefffe448d73c1c','per_kit','per_kit_stock'),
      (0x40006158,'4fefffb848d7041c','per_root_encoder','per_root_encoder_stock'),
      (0x4003c134,'4e56ff9848d73cfc','per_config','per_config_stock'),
      (0x400764ec,'2f0a226f0008206f000c','per_key_bridge','per_key_bridge_stock'),
      (0x4001aa4e,'4fefffe048d70cfc','per_level','per_level_stock'),
      (0x4001f4f0,'4e56ffac48d73cfc','per_parameter','per_param_stock'),
      (0x4001c0d2,'4e56ffa848d73c7c','per_main_key','per_key_stock'),
      (0x4001f97e,'4e56ffd848d73c0c','per_parameter_key','per_param_key_stock'),
      (0x400582d0,'2f0a202f00082200','per_publish','per_publish_stock'),
      (0x40058308,'4fefffdc202f0028','per_incremental','per_incremental_stock'),
      (0x4001b22a,'4e56ffc048d73cfc','per_draw','per_draw_stock')]
    for a,raw,hook,original in hooks:
        require(stock[a-BASE:a-BASE+len(raw)//2]==bytes.fromhex(raw),'Prologue natif inattendu')
        replay.extend([f'.globl {original}',f'{original}:','.byte '+','.join('0x'+raw[i:i+2] for i in range(0,len(raw),2)),f'jmp 0x{a+len(raw)//2:x}'])
    irq_hooks=[(0x40054d70,'23c040a7888c','per_irq_immediate'),(0x4005571e,'23d640a78888','per_irq_boundary'),(0x40055510,'23d640a78888','per_irq_stop')]
    for address,raw,name in irq_hooks:
        require(stock[address-BASE:address-BASE+6]==bytes.fromhex(raw),'Instruction IRQ inattendue')
        replay.extend([f'.globl {name}',f'{name}:','.byte '+','.join('0x'+raw[i:i+2] for i in range(0,len(raw),2)),
          'lea -24(%sp),%sp','movem.l %d0-%d1/%a0-%a1,(%sp)','move.w %sr,%d0','move.l %d0,16(%sp)',
          'jsr per_storage_observe','move.l 16(%sp),%d0','move.w %d0,%sr','movem.l (%sp),%d0-%d1/%a0-%a1','lea 24(%sp),%sp','rts'])
    (out/'stock-replay.s').write_text('\n'.join(replay)+'\n')
    (out/'payload.ld').write_text(f'SECTIONS {{ . = 0x{RUNTIME:x}; .text : {{ *(.text) }} .rodata : {{ *(.rodata) }} .data : {{ *(.data) }} ASSERT(. <= 0x42340000, "Static performance payload exceeds bounded RAM window") }}')
    run(CROSS+'gcc','-mcpu=54418','-msoft-float','-Os','-ffreestanding','-fno-builtin','-fno-jump-tables','-fno-tree-switch-conversion','-fomit-frame-pointer','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-I',str(out),'-c',str(SRC/'performance15.c'),'-o',str(out/'payload.o'))
    run(CROSS+'as','-mcpu=54418',str(out/'stock-replay.s'),'-o',str(out/'stock-replay.o'))
    run(CROSS+'gcc','-mcpu=54418','-msoft-float','-nostdlib','-Wl,-T,'+str(out/'payload.ld'),'-o',str(out/'payload.elf'),str(out/'payload.o'),str(out/'stock-replay.o'),'-lgcc')
    run(CROSS+'objcopy','-O','binary',str(out/'payload.elf'),str(out/'payload.bin'))
    nm=subprocess.check_output([CROSS+'nm','-n',str(out/'payload.elf')],text=True)
    symbols={m[2]:int(m[1],16) for l in nm.splitlines() if (m:=re.match(r'([0-9a-f]+)\s+\w\s+(\S+)',l))}
    payload=(out/'payload.bin').read_bytes();b=bytearray(stock);changes=[]
    def patch(a,before,after,label):
        before=bytes.fromhex(before);offset=a-BASE
        require(b[offset:offset+len(before)]==before,'Octets old inattendus')
        require(len(before)==len(after),'Longueur de detour incorrecte')
        b[offset:offset+len(before)]=after
        changes.append(dict(address=hex(a),before=before.hex(),after=after.hex(),label=label))
    for a,raw,hook,original in hooks:
        patch(a,raw,b'\x4e\xf9'+struct.pack('>I',symbols[hook])+b'\x4e\x71'*((len(raw)//2-6)//2),hook)
    for address,raw,name in irq_hooks:
        patch(address,raw,b'\x4e\xb9'+struct.pack('>I',symbols[name]),'observe actual sequencer activation; original store and register/SR state preserved')
    for address,opcode in [(0x40010af8,'4bf9'),(0x40010d10,'4bf9'),(0x4001199a,'49f9'),(0x40011b18,'43f9'),(0x40061774,'45f9'),(0x400617b6,'47f9')]:
        patch(address,opcode+'4008f1f0',bytes.fromhex(opcode)+struct.pack('>I',symbols['per_kit_copy']),'native pattern copy/paste/undo and project initialization copy helper')
    for address,original,wrapper in [(0x400fe34c,0x400d3b3c,'per_clip_destroy'),(0x400fe350,0x400d3bd6,'per_clip_delete')]:
        patch(address,struct.pack('>I',original).hex(),struct.pack('>I',symbols[wrapper]),'pattern clipboard lifecycle releases macro sidecar')
    patch(0x400081f2,'4eb940090f48',b'\x4e\xb9'+struct.pack('>I',symbols['per_tick']),'UI gesture release tracking before native dispatch')
    patch(0x4000891c,'4eb94000637a',b'\x4e\xb9'+struct.pack('>I',symbols['per_power']),'MAIN VOLUME short-release reset; native power preserved')
    patch(0x400597a8,'4eb940058474',b'\x4e\xb9'+struct.pack('>I',symbols['per_audio_levels']),'track and global FX offsets in native smoothing targets; canonical source preserved')
    loader=BASE+len(stock)
    (out/'loader.s').write_text(f'''.text
.globl boot_loader
boot_loader:
 move.l %d0,-(%sp)
 move.l %a2,-(%sp)
 pea .Lafter_stock
 move.l %a2,-(%sp)
 lea 0x4019b590,%a2
 jmp 0x40000464
.Lafter_stock:
 lea payload_source,%a2
 lea 0x{RUNTIME:x},%a0
 move.l #{(len(payload)+3)//4},%d0
.Lcopy:
 move.l (%a2)+,(%a0)+
 subq.l #1,%d0
 bne.s .Lcopy
 move.l (%sp)+,%a2
 move.l (%sp)+,%d0
 rts
.balign 4
payload_source:
.incbin "build/performance15/payload.bin"
.balign 4
''')
    (out/'loader.ld').write_text(f'SECTIONS {{ . = 0x{loader:x}; .text : {{ *(.text) }} }}')
    run(CROSS+'as','-mcpu=54418',str(out/'loader.s'),'-o',str(out/'loader.o'))
    run(CROSS+'ld','-T',str(out/'loader.ld'),'-o',str(out/'loader.elf'),str(out/'loader.o'))
    run(CROSS+'objcopy','-O','binary',str(out/'loader.elf'),str(out/'loader.bin'))
    patch(0x4000045c,'2f0a45f94019b590',b'\x4e\xf9'+struct.pack('>I',loader)+b'\x4e\x71','copy payload before stock BSS clear')
    b.extend((out/'loader.bin').read_bytes())
    require(BASE+len(b)<=native_build.END_LIMIT,'Charge utile au-dela de la borne du bootstrap')
    (out/'mainos.bin').write_bytes(b)
    manifest=dict(schema=1,status='experimental',cpu='54418',
      stock_syx_sha256=SOURCE_SHA,stock_main_sha256=STOCK_SHA,
      main_sha256=hashlib.sha256(b).hexdigest(),payload_sha256=hashlib.sha256(payload).hexdigest(),
      runtime_address=hex(RUNTIME),runtime_bytes=len(payload),loader_address=hex(loader),
      changes=changes,symbols={k:hex(v) for k,v in symbols.items()})
    # Verification par le moteur amont des memes ecritures old/new.
    writes=[dict(off=int(c['address'],16)-BASE,old=c['before'],new=c['after']) for c in changes]
    checked,_=native_build.apply_writes(stock,[dict(id='performance15',writes=writes)])
    require(bytes(b[:len(stock)])==checked,'Verification des ecritures amont differente')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return stock,bytes(b),manifest


def package(cycles,patched,output):
    """Reconstruit localement le SysEx ; ne change que la section 3."""
    import aplib_grow
    require(Path(cycles).resolve()!=Path(output).resolve(),'Ne pas ecraser le fichier officiel')
    raw=Path(cycles).read_bytes();require(hashlib.sha256(raw).hexdigest()==SOURCE_SHA,'OS officiel requis au reconditionnement')
    stream,syx=unwrap(raw);info=container.parse(stream)
    section=next(s for s in info['sections'] if s['id']==3)
    stock,ops=aplib.depack(info['blob'][section['off']:section['off']+section['size']])
    dirty=bytearray(a!=b for a,b in zip(stock,patched))+bytearray([1])*(len(patched)-len(stock))
    packed=aplib_grow.repack_grow(patched,ops,dirty,len(stock));require(aplib.depack(packed)[0]==patched,'Relecture aPLib differente')
    plain=[]
    for s in info['sections']:
        try:plain.append(aplib.depack(info['blob'][s['off']:s['off']+s['size']])[0])
        except Exception:pass
    key=container.find_key(plain,info['blob'][:-32],info['blob'][-32:]);require(bool(key),'Cle de controle HMAC introuvable')
    blob=container.rebuild(info,{3:packed},key)
    data=wrap(container.build_stream(blob,BYTES_PER_MSG),syx['product'],syx['start_seq'])
    reread,_=unwrap(data);check=container.parse(reread)
    for original,new in zip(info['sections'],check['sections']):
        a=info['blob'][original['off']:original['off']+original['size']]
        b=check['blob'][new['off']:new['off']+new['size']]
        require(aplib.depack(b)[0]==patched if original['id']==3 else a==b,'Section modifiee ou relecture incorrecte')
    require(container.find_key(plain,check['blob'][:-32],check['blob'][-32:])==key,'HMAC de sortie incorrect')
    Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_bytes(data)


def reference(manifest):
    return {k:manifest[k] for k in ('cpu','stock_syx_sha256','stock_main_sha256','main_sha256',
        'payload_sha256','runtime_address','runtime_bytes','loader_address')}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True)
    ap.add_argument('--check',action='store_true',help='compare la reference versionnee')
    ap.add_argument('--update-reference',action='store_true',help='met a jour les seules empreintes de reference')
    ap.add_argument('--output',help='SysEx local facultatif ; jamais versionne')
    args=ap.parse_args();_,patched,m=compile_mode(args.cycles);ref=SRC/'reference.json'
    if args.update_reference:ref.write_text(json.dumps(reference(m),indent=2)+'\n')
    if args.check and (not ref.exists() or json.loads(ref.read_text())!=reference(m)):
        raise SystemExit('Reference differente : verifier le compilateur et les sources')
    if args.output:package(args.cycles,patched,args.output)
    print('Performance15 :',m['runtime_bytes'],'octets ; MAIN OS',m['main_sha256'])


if __name__=='__main__':main()
