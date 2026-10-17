"""Note 102 : remplacer en place le ladder partage, sans nouveau chargeur."""
import argparse,hashlib,json,pathlib,shutil,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from gen_seq_gen import symbols

def generate(source=None):
 w=json.loads((ROOT/'firmware/wizard-catalogue.json').read_text())['variants']['0']['wizard'];s={k:int(v,16) for k,v in w['symbols'].items()};ap=w['append'];base=int(ap['dest'],16)
 at=s['gflt_run'];limit=s['sampler_com_gate'];raw=bytearray.fromhex(ap['parts'][0]['hex'])
 c=(ROOT/'docs/flasher/continuous-filter.js').read_text();c=json.loads(c[c.index('={')+1:c.index(';')])
 for ch in c['payload']:
  if base+ch['off']>=at and base+ch['off']<limit:
   i=ch['off'];assert raw[i:i+len(ch['old'])//2].hex()==ch['old'];raw[i:i+len(ch['new'])//2]=bytes.fromhex(ch['new'])
 old=bytes(raw[at-base:limit-base]);cross=next(p for p in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(p+'as'))
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'f.o'),str(source or ROOT/'tools/machines/track_filter/precision.s')],check=True)
  defs={k.upper():s[v] for k,v in [('gflt_f','gflt_f'),('gflt_q','gflt_q'),('gflt_mk','gflt_mk'),('gflt_y1','gflt_y1')]}
  (p/'f.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { .text '+hex(at)+' : SUBALIGN(2) { *(.text) } }')
  subprocess.run([cross+'ld','-T',str(p/'f.ld'),'-o',str(p/'f.elf'),str(p/'f.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'f.elf'),str(p/'f.bin')],check=True);code=(p/'f.bin').read_bytes()
  sy=symbols(cross,p/'f.elf')
 assert len(code)<=len(old),(len(code),len(old))
 result={'at':at,'size':len(old),'old_sha256':hashlib.sha256(old).hexdigest(),'hex':(code+b'\x4e\x71'*((len(old)-len(code))//2)).hex(),'code_size':len(code)}
 if 'precise_modes' in sy:
  result['mode_address']=sy['precise_modes'];result['probe_size']=sy['precise_modes']-at
  fingerprint=2166136261
  for byte in code[:result['probe_size']]:fingerprint=((fingerprint^byte)*16777619)&0xffffffff
  result['probe_hash']=fingerprint
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();d=generate();text='window.MCFilterPrecision='+json.dumps(d,separators=(',',':'))+';\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok ladder haute precision',d['code_size'],'/',d['size'],'octets ; aucun chargeur/BSS ajoute')
if __name__=='__main__':main()
