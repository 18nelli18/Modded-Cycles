"""Export SAMP3.00 : vue canonique des RSG1 sans modifier les fichiers."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x4693a000;BSS=0x4693b100
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='67a50eced194bcd4387a863a9bdcf6a205b9c2fa75bb72c5c28e93315066041e');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
am=m['activity_masks'];prev=m.get('chord_storage300') or m.get('dummy300') or m['cpu_monitor'];previous=am['symbols']['am_boot_finish'];old=json.loads((R/'tools/machines/md/base-map.json').read_text())['tg']
aliases=dict(ex_id_mode=old['id_mode'])
assert image[0x4009249a-BASE:0x400924a0-BASE]==b'\x4e\xb9'+struct.pack('>I',old['rpc_type'])
assert image[0x40089ec4-BASE:0x40089eca-BASE].hex()=='283c4007c0e8'
assert image[0x40094a04-BASE:0x40094a0a-BASE].hex()=='2f0a206f0008'
assert image[0x400888be-BASE:0x400888c4-BASE].hex()=='4eb94007bf38'
assert image[0x40094c9a-BASE:0x40094ca0-BASE]==b'\x4e\xf9'+struct.pack('>I',old['rpc_ot'])
# Extraction des fonctions natives de hash ; leur etat devient prive au transfert.
hashcode=bytearray(stock[0x4007d9c0-BASE:0x4007ddee-BASE]);relocations=[]
for i in range(0,len(hashcode)-3,2):
 v=int.from_bytes(hashcode[i:i+4],'big')
 if 0x4027cca4<=v<=0x4027d160:
  struct.pack_into('>I',hashcode,i,BSS+v-0x4027cca4);relocations.append(i)
assert len(relocations)>20
(O/'hash-native.bin').write_bytes(hashcode)
asm=f""".text
.globl ex_hash_final,ex_hash_update,ex_install,ex_type,ex_output,vx_open_hook
ex_hash_final:
.incbin \"{(O/'hash-native.bin').resolve().as_posix()}\"
.set ex_hash_update,ex_hash_final+0x2f2
ex_type:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 20(%sp),-(%sp)
 jsr ex_request
 addq.l #4,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp {old['rpc_type']:#x}
ex_output:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 20(%sp),-(%sp)
 jsr ex_send
 addq.l #4,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 move.l %a2,-(%sp)
 movea.l 8(%sp),%a0
 jmp 0x40094a0a
vx_open_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l %a5,-(%sp)
 jsr vx_invalidate
 addq.l #4,%sp
 move.l 76(%a5),-(%sp)
 jsr vx_open
 addq.l #4,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 move.l #0x4007c0e8,%d4
 jmp 0x40089eca
ex_install:
 lea -8(%sp),%sp
 movem.l %d0/%a1,(%sp)
 lea 0x40089ec4,%a1
 move.w #0x4ef9,(%a1)+
 move.l #vx_open_hook,(%a1)
 lea 0x400888be,%a1
 move.w #0x4eb9,(%a1)+
 move.l #vx_read,(%a1)
 lea 0x4009249a,%a1
 move.w #0x4eb9,(%a1)+
 move.l #ex_type,(%a1)
 lea 0x40094a04,%a1
 move.w #0x4ef9,(%a1)+
 move.l #ex_output,(%a1)
 movem.l (%sp),%d0/%a1
 lea 8(%sp),%sp
 jmp {previous:#x}
.section .hashbss,\"aw\",@nobits
.globl ex_hash_state
ex_hash_state: .skip 1216
"""
(O/'bridge.S').write_text(asm)
(O/'module.ld').write_text('SECTIONS { .text '+hex(CODE)+' : { *(.text*) *(.rodata*) } .bss '+hex(BSS)+' (NOLOAD) : { *(.hashbss) *(.bss*) *(COMMON) } . = ALIGN(4); ex_end = .; }\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
run('gcc','-mcpu=54418','-c',O/'bridge.S','-o',O/'bridge.o');run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',R/'tools/machines/track_fx/transfer-native300.c','-o',O/'transfer.o');run('ld','-T',O/'module.ld','-o',O/'module.elf',O/'bridge.o',O/'transfer.o');run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=BSS and s['ex_end']<=0x4693e000 and s['ex_hash_state']==BSS
# Verifier les intervalles complets, pas seulement le debut de la BSS ACID.
new_ranges=[('code',CODE,CODE+len(blob)),('bss',BSS,s['ex_end'])]
for module,meta in m.items():
 if not isinstance(meta,dict):continue
 ranges=[]
 if isinstance(meta.get('code'),int) and isinstance(meta.get('code_bytes'),int):ranges.append(('code',meta['code'],meta['code']+meta['code_bytes']))
 if isinstance(meta.get('bss'),int) and isinstance(meta.get('bss_end'),int):ranges.append(('bss',meta['bss'],meta['bss_end']))
 if isinstance(meta.get('wizard_bss'),int) and isinstance(meta.get('wizard_bss_end'),int):ranges.append(('wizard_bss',meta['wizard_bss'],meta['wizard_bss_end']))
 for label,begin,finish in ranges:
  for new_label,lo,hi in new_ranges:assert hi<=begin or lo>=finish,('memory overlap',new_label,module,label,hex(lo),hex(hi),hex(begin),hex(finish))
# Les quatre detours figurent aussi dans l image chargee avant activation du cache.
# La copie tardive reste idempotente pour les anciennes chaines de boot.
for at,opcode,target in ((0x40089ec4,0x4ef9,s['vx_open_hook']),(0x400888be,0x4eb9,s['vx_read']),(0x4009249a,0x4eb9,s['ex_type']),(0x40094a04,0x4ef9,s['ex_output'])):
 struct.pack_into('>HI',image,at-BASE,opcode,target)
lo=prev['loader']+512-BASE;old=b'\x4e\xf9'+struct.pack('>I',previous);chunk=bytes(image[lo:lo+prev['code_bytes']]);assert chunk.count(old)==1;patchat=lo+chunk.index(old)+2;struct.pack_into('>I',image,patchat,s['ex_install']);relay_patch=BASE+patchat
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(s["ex_end"]-BSS)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
(O/'load.S').write_text(load);run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','cal_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob
from title204_assets import apply
# Identifiant experimental distinct ; aucun push/flasher modifie.
def patch(at,old,new,buf):assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
m['title_screen']=apply(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,patch,'3.00',lite=not am['full'],previous=m['title_screen'])
# Tokens de compression officiels, comme les generateurs prives existants.
stockops=read(a.cycles)[3];dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),stockops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
plains=[]
for sec in pkg['sections']:
 try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
 except Exception:pass
key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_3.00_Release.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
m['transfer300']=dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_end=s['ex_end'],symbols=s,aliases=aliases,loader=loader,boot_target=s['ex_install'],boot_relay_patch=relay_patch,source_sha256=sha(a.source.read_bytes()),read_only=True,normalizes_existing_RSG1=True,native_file_ownership=True,no_secondary_open_close=True,no_IO_in_RPC_parser_serializer=True,hardware_tested=False)
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT transfer export',len(blob),'code bytes',sha(result),flush=True)
