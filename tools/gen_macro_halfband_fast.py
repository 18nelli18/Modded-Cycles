"""Note124 : noyau MACRO162octets, reference C propre et sortie reproductible."""
import argparse,hashlib,json,pathlib,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=ROOT/'build/macro-optimization';out.mkdir(exist_ok=True)
 cross=next((c for c in ['m68k-linux-gnu-','m68k-elf-'] if shutil.which(c+'as')),'m68k-linux-gnu-')
 subprocess.run([cross+'as','-mcpu=54418',str(ROOT/'tools/machines/macro/halfband_fast.s'),'-o',str(out/'halfband.o')],check=True)
 subprocess.run([cross+'objcopy','-O','binary','-j','.text',str(out/'halfband.o'),str(out/'halfband.bin')],check=True)
 new=(out/'halfband.bin').read_bytes();t=json.loads((ROOT/'tweaks/model-cycles_OS1.13/25-macro.json').read_text(encoding='utf-8'));part=t['append']['parts'][0];at=int(t['symbols']['macro_render'],16)-int(part['dest'],16)+0xea;old=bytes.fromhex(part['hex'])[at:at+162]
 assert len(new)==len(old)==162 and old[:8].hex()=='5888756800187d68'
 text='window.MCMacroHalfband='+json.dumps(dict(old=old.hex(),hex=new.hex(),old_sha256=hashlib.sha256(old).hexdigest(),new_sha256=hashlib.sha256(new).hexdigest(),size=162),separators=(',',':'))+';\n';target=out/'macro-halfband-data.js'
 if a.check:assert target.read_text(encoding='utf-8')==text
 else:target.write_text(text,encoding='utf-8')
 print('PASS meme taille162, filtre demi-bande propre, aucun firmware exporte')
if __name__=='__main__':main()
