#!/usr/bin/env python3
"""Bootstrap ChordKeys seul : prototype local, pas encore au catalogue.

Les deux masques du loader MIDI sont libres sans Banque. Réutiliser son
décompresseur propre MIT ; aucune fonction ni donnée musicale Banque/TG.
La combinaison avec ces mods exigera un bootstrap commun, encore à faire.
"""
import argparse,json,pathlib,struct,subprocess,tempfile
import build,sprites,aplib_cost
from chord_keys_pr87 import load_stock

def generate(stock,payload,bank,tg=None,engine=None,source_at=None):
 start=int(payload['parts'][0]['dest'],16);raw=bytes.fromhex(payload['parts'][0]['hex']);clear=(start+len(raw)+15)&~15;source=build.BASE+len(stock)
 if tg:source=int(tg['append']['at'],16)+tg['append']['size']
 if source_at is not None:source=int(source_at,0) if isinstance(source_at,str) else source_at
 assert not engine or source_at is not None,'source fixe requise avec moteurs'
 preserve_tg=''
 if tg:
  preserve_tg=f''' cmpal #{tg['symbols']['blob_start']},%a0
 bne 4f
 moveal #{tg['symbols']['reserved_end']},%a0
4:
'''
 pad_source=(pathlib.Path(__file__).parent/'machines/midi_play_ui/controls.s').read_text().split('mpu_pad:',1)[1].split('    .data',1)[0]
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d)
  (p/'boot.s').write_text(f'''.text
.globl chord_boot,chord_clear,chord_resume
chord_boot:
 lea {source:#x},%a0
 lea {start:#x},%a1
 lea %sp@(-24),%sp
 moveml %d2-%d6/%a2,%sp@
 jsr 0x40167c50
 moveml %sp@,%d2-%d6/%a2
 lea %sp@(24),%sp
 nop
 movel #0x000cc100,%d0
 movec %d0,%cacr
 nop
 jmp chord_clear
.section .clear,"ax"
chord_clear:
 lea %sp@(-16),%sp
 moveml %d4-%d7,%sp@
 movel #0x4c03e000,%d4
 movec %d4,%acr1
 lea 0x4019b590,%a0
 moveq #0,%d4
 moveq #0,%d5
 moveq #0,%d6
 moveq #0,%d7
1:
{preserve_tg} cmpal #{start&~15:#x},%a0
 bne 2f
 moveal #chord_end,%a0
2: cmpal #0x423380b0,%a0
 bcc 3f
 moveml %d4-%d7,%a0@
 lea %a0@(16),%a0
 bra 1b
3: moveml %sp@,%d4-%d7
 lea %sp@(16),%sp
 lea 0xfc044000,%a0
chord_resume:
 jmp 0x4000053a
.globl mpu_pad
mpu_pad:
{pad_source}
.balign 16
chord_end:
''')
  (p/'boot.ld').write_text(f"CK_HELD_PADS = {payload['symbols']['held_pads']};\nCK_PAD = {payload['symbols']['ck_ui_pad']};\nSECTIONS {{ .text 0x401907a4 : {{ *(.text) }} .clear {clear:#x} : {{ *(.clear) }} }}")
  subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(p/'boot.o'),str(p/'boot.s')],check=True)
  subprocess.run(['m68k-elf-ld','-T',str(p/'boot.ld'),'-o',str(p/'boot.elf'),str(p/'boot.o')],check=True)
  chunks={}
  for section in ['text','clear']:
   subprocess.run(['m68k-elf-objcopy','-O','binary','--only-section=.'+section,str(p/'boot.elf'),str(p/(section+'.bin'))],check=True);chunks[section]=(p/(section+'.bin')).read_bytes()
  symbols={row[2]:hex(int(row[0],16)) for line in subprocess.check_output(['m68k-elf-nm',str(p/'boot.elf')],text=True).splitlines() if len(row:=line.split())==3}
 assert len(chunks['text'])<=sprites.MASKS[0x401907a4][0]
 raw=bytearray(raw+bytes(clear-start-len(raw))+chunks['clear'])
 thunk=int(payload['symbols']['ck_ui_pad_thunk'],16)-start
 expected=bytes.fromhex('51af000451af00044ef9')+struct.pack('>I',int(payload['symbols']['ck_ui_pad'],16))
 assert raw[thunk:thunk+14]==expected
 raw[thunk+10:thunk+14]=struct.pack('>I',int(symbols['mpu_pad'],16))
 packed=aplib_cost.pack(bytes(raw),depth=512,lazy=True)
 writes=[dict(w) for w in payload['writes']]
 primary=next(w for w in writes if w['off']==0x4010025c-build.BASE)
 assert primary['new']==struct.pack('>I',int(payload['symbols']['ck_ui_pad'],16)).hex()
 primary['new']=struct.pack('>I',int(symbols['mpu_pad'],16)).hex()
 for at,code in [(0x401907a4,chunks['text']),(0x40167c50,bytes.fromhex(next(w['new'] for w in bank['writes'] if w['off']==0x40167c50-build.BASE)))]:
  writes.extend([dict(off=at-build.BASE,old=stock[at-build.BASE:at-build.BASE+len(code)].hex(),new=code.hex()),sprites.redirect_write(at)])
 if engine:
  expected=b'\x4e\xf9'+struct.pack('>I',int(tg['symbols']['boot_extra_hook'],16)) if tg else bytes.fromhex('4feffff048d700f04ef9400004ba')
  hits=[]
  for w in engine['writes']:
   code=bytes.fromhex(w['new'])
   for off in range(0,len(code)-len(expected)+1,2):
    if code[off:off+len(expected)]==expected:hits.append((w['off']+off,expected))
  assert len(hits)==1,('reprise moteur ambiguë',engine['id'],hits)
  at,old=hits[0];writes.append(dict(off=at,old=old.hex(),new=(bytes.fromhex('4ef9401907a4')+b'\x4e\x71'*((len(old)-6)//2)).hex()))
 elif tg:writes.append(dict(off=0x40000532-build.BASE,old=struct.pack('>I',int(tg['symbols']['boot_extra_hook'],16)).hex(),new='401907a4'))
 else:
  at=0x40000530;writes.append(dict(off=at-build.BASE,old=stock[at-build.BASE:at-build.BASE+10].hex(),new='4ef9401907a44e714e71'))
 dependencies=([tg['id']] if tg else [])+([engine['id']] if engine else [])
 # Exclure le préfixe contenant le runtime du vrai LRU disque.
 # Le placement sans TG peut se limiter au premier bloc de 16 KiB.
 base,_=build.apply_writes(stock,([tg] if tg else [])+([engine] if engine else []))
 cache_blocks=(clear+len(chunks['clear'])-0x401ab750+16383)//16384
 assert 1<=cache_blocks<16
 assert clear+len(chunks['clear'])<=0x401ab750+cache_blocks*16384
 for at,new in [(0x400792f2,0x401eb750+20*cache_blocks),(0x400792bc,0x401eb750+20*(cache_blocks+1)+16)]:
  writes.append(dict(off=at-build.BASE,old=bytes(base[at-build.BASE:at-build.BASE+4]).hex(),new=struct.pack('>I',new).hex()))
 t={'id':'chord-independent-tg-prototype' if tg else 'chord-independent-prototype','order':45,'status':'experimental','flashable':False,'requires':dependencies,'conflicts':[],
    'writes':sorted(writes,key=lambda w:w['off']),'symbols':dict(payload['symbols'],**symbols),
    'append':{'at':hex(source),'dest':hex(start),'size':len(raw),'parts':[{'dest':hex(start),'hex':raw.hex()}],'reloc':[],'compress':'aplib','compressed_hex':packed.hex()},
    'cache_blocks':cache_blocks,'pending':['full_lifecycle_and_audio_proofs','hardware_test'],'prototype_only':True}
 if source_at is not None:t['append']['zero_pad_from']=hex(build.BASE+len(stock))
 build.apply_writes(stock,([tg] if tg else [])+([engine] if engine else [])+[t]);return t

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--payload',required=True);p.add_argument('--bank',required=True);p.add_argument('--tg');p.add_argument('--engine');p.add_argument('--source');p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 read=lambda name:json.loads(pathlib.Path(name).read_text()) if name else None
 t=generate(load_stock(a.cycles),read(a.payload),read(a.bank),read(a.tg),read(a.engine),a.source);text=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : prototype boot Chord, dépendances explicites',t['requires'],'; catalogue inchangé')
if __name__=='__main__':main()
