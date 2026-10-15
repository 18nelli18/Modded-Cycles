"""Générer d'abord et intro demi-durée ; mêmes adresses publiques du menu."""
import pathlib,subprocess,struct,copy
import build,sprites
ROOT=pathlib.Path('work/genie-quick-access')
def patch(t,stock):
 t=copy.deepcopy(t)
 if 'sg_map_row' not in t.get('symbols',{}):return t
 s=t['symbols'];base=int(s['sg_ui_last'],16);oldmap=int(s['sg_map_row'],16);oldun=int(s['sg_unmap_row'],16)
 w=next(w for w in t['writes'] if w['off']+build.BASE==base)
 old=bytes.fromhex(w['new']);assert len(old)==28 and old[:4]==bytes.fromhex('70144e75')
 address=base+len(old)
 subprocess.run(['m68k-elf-ld','-Ttext='+hex(address),'-e','sg_ui_last','-o',str(ROOT/'patch.elf'),str(ROOT/'rows.o')],check=True)
 subprocess.run(['m68k-elf-objcopy','-O','binary',str(ROOT/'patch.elf'),str(ROOT/'patch.bin')],check=True)
 syms={r[2]:int(r[0],16) for l in subprocess.check_output(['m68k-elf-nm',str(ROOT/'patch.elf')],text=True).splitlines() if len(r:=l.split())==3}
 b=bytearray(old)
 for at,name in [(oldmap,'sg_map_row'),(oldun,'sg_unmap_row')]:b[at-base:at-base+6]=b'\x4e\xf9'+struct.pack('>I',syms[name])
 b+= (ROOT/'patch.bin').read_bytes();assert len(b)<=sprites.MASKS[base][0]
 assert not any(x is not w and x['off']<w['off']+len(b) and w['off']<x['off']+len(bytes.fromhex(x['new'])) for x in t['writes'])
 w['old']=stock[w['off']:w['off']+len(b)].hex();w['new']=b.hex()
 hits=0
 for w in t['writes']:
  b=bytes.fromhex(w['new']);hits+=b.count(bytes.fromhex('0c80000005dc'));w['new']=b.replace(bytes.fromhex('0c80000005dc'),bytes.fromhex('0c80000002ee')).hex()
 assert hits==1,(t['id'],hits)
 return t
