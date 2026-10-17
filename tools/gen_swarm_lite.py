"""Note 107 : trois oscillateurs SWARM ; aucun octet OS exporte."""
import argparse,pathlib,sys,subprocess,hashlib,json,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools/emu'))
import syntakt

def main():
 cross=next((c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'gcc')),'m68k-linux-gnu-')
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=ROOT/'build/swarm-lite';out.mkdir(parents=True,exist_ok=True)
 subprocess.run([cross+'gcc','-mcpu=54418','-c',str(ROOT/'tools/machines/syntakt_load/lite_sum.s'),'-o',str(out/'sum.o')],check=True)
 subprocess.run([cross+'objcopy','-O','binary','--only-section=.text',str(out/'sum.o'),str(out/'sum.bin')],check=True)
 body=(out/'sum.bin').read_bytes();assert len(body)==44
 img=syntakt.dsp_image(str(ROOT/'firmware/Syntakt_OS1.42.syx'))
 edits=[]
 for at,own in [(x,bytes.fromhex('4e71')) for x in (0x40009758,0x40009760,0x40009774,0x4000977c)]+[(0x40009790,body)]:
  old=img[at-0x40000400:at-0x40000400+len(own)];edits.append(dict(source=at,size=len(own),old_sha256=hashlib.sha256(old).hexdigest(),hex=own.hex()))
 subprocess.run([cross+'gcc','-mcpu=54418','-c',str(ROOT/'tools/machines/syntakt_load/recurrence.s'),'-o',str(out/'recurrence.o')],check=True)
 subprocess.run([cross+'objcopy','-O','binary','--only-section=.text',str(out/'recurrence.o'),str(out/'recurrence.bin')],check=True)
 own=(out/'recurrence.bin').read_bytes();assert len(own)<=62;own+=bytes.fromhex('4e71')*((62-len(own))//2)
 exact=dict(source=0x40006074,size=62,old_sha256=hashlib.sha256(img[0x40006074-0x40000400:0x40006074-0x40000400+62]).hexdigest(),hex=own.hex())
 text='window.MCSwarmLite='+json.dumps(dict(edits=edits,exact=[exact],oscillators=[0,3,6]),separators=(',',':'))+';\n';target=out/'swarm-lite-data.js'
 if a.check:assert target.read_text()==text
 else:target.write_text(text)
 print('PASS SWARM lite : trois oscillateurs, six gardes SHA, code propre seulement')
if __name__=='__main__':main()
