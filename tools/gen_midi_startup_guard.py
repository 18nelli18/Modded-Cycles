#!/usr/bin/env python3
"""Candidat diagnostic sans TG : pas de service Banque avant ouverture.

Ne prétend pas résoudre l'écran blanc matériel. Protège les callbacks LED
avant publication des singletons UI/MIDI ; firmware principal inchangé.
"""
import argparse,copy,json,pathlib,struct,subprocess,tempfile
import build,aplib_dense

def generate(data):
 data=copy.deepcopy(data)
 if data['core']['id']!='performance-core':return data
 bank=data['bank'];ap=bank['append'];origin=int(ap['dest'],16);raw=bytearray.fromhex(ap['parts'][0]['hex']);start=(origin+len(raw)+3)&~3
 s={k:int(v,16) for k,v in bank['symbols'].items()};core=data['core']['symbols'];led=int(core['led_hook'],16)
 prologue=bytes.fromhex('4fefffd048d70fff');off=led-origin
 assert raw[off:off+8]==prologue
 source=f'''.text
.globl ml_safe_ui,core_safe_led
ml_safe_ui:
 tstl {s['ml_context']:#x}
 beq .Lui_done
 tstl 0x40fe4178
 beq .Lui_done
 tstl 0x40fe4228
 beq .Lui_done
 jmp {s['ml_ui_drain']:#x}
.Lui_done:
 rts
core_safe_led:
 lea %sp@(-48),%sp
 moveml %d0-%d7/%a0-%a3,%sp@
 tstl 0x40fe4178
 beq .Lled_done
 tstl 0x40fe4228
 beq .Lled_done
 jmp {led+8:#x}
.Lled_done:
 moveml %sp@,%d0-%d7/%a0-%a3
 lea %sp@(48),%sp
 rts
'''
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d);(p/'guard.s').write_text(source)
  subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(p/'guard.o'),str(p/'guard.s')],check=True)
  subprocess.run(['m68k-elf-ld','-Ttext='+hex(start),'-e','ml_safe_ui','-o',str(p/'guard.elf'),str(p/'guard.o')],check=True)
  subprocess.run(['m68k-elf-objcopy','-O','binary',str(p/'guard.elf'),str(p/'guard.bin')],check=True)
  code=(p/'guard.bin').read_bytes();syms={r[2]:int(r[0],16) for line in subprocess.check_output(['m68k-elf-nm',str(p/'guard.elf')],text=True).splitlines() if len(r:=line.split())==3}
 raw[off:off+8]=bytes.fromhex('4ef9')+struct.pack('>I',syms['core_safe_led'])+bytes.fromhex('4e71')
 target=bytes.fromhex('4eb9')+struct.pack('>I',s['ml_ui_drain']);lo=s['ml_ui_hook']-origin;hi=lo+64;sites=[i for i in range(lo,hi,2) if raw[i:i+6]==target]
 assert len(sites)==1;raw[sites[0]+2:sites[0]+6]=struct.pack('>I',syms['ml_safe_ui'])
 raw+=bytes(start-origin-len(raw))+code;end=(origin+len(raw)+15)&~15;raw+=bytes(end-origin-len(raw))
 oldend=s['ML_BANK_END'];skip=s['ml_boot_skip']-origin;assert raw[skip:skip+6]==bytes.fromhex('207c')+struct.pack('>I',oldend)
 raw[skip+2:skip+6]=struct.pack('>I',end)
 blocks=(len(raw)+16383)//16384
 assert blocks==bank['cache_blocks'],'adapter les références cache avant publication'
 packed=aplib_dense.pack(bytes(raw),depth=128);assert int(ap['at'],16)+len(packed)<=build.END_LIMIT
 ap.update(size=len(raw),parts=[{'dest':hex(origin),'hex':raw.hex()}],compressed_hex=packed.hex())
 bank['symbols'].update({k:hex(v) for k,v in syms.items()},ML_BANK_END=hex(end))
 data['startup_guard']={'status':'diagnostic','deferred_until_bank_open':True,'hardware_fix_verified':False}
 return data

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 data=generate(json.loads(pathlib.Path(a.candidate).read_text()));text=json.dumps(data,indent=1,ensure_ascii=False)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : garde démarrage diagnostic ; aucune correction matérielle revendiquée')
if __name__=='__main__':main()
