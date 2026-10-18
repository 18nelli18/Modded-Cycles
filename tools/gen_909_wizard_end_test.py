"""Test909 : separer Sample End du descripteur binaire RC Type.

Le slot son12 et les locks restent identiques. Wizard utilise un autre
descripteur natif du meme slot, continu0..127 ; aucun DSP909 n'est modifie.
Le cas de reference est produit par test_909_current.js depuis909.7.
"""
import argparse,json,pathlib,re,shutil,sys,tempfile,struct
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_midi_entry import boot_case
STAMP='2026-10-18-909-wizard-end-test-1'
def make_data(case):
 img,mem,ts=boot_case(case);wizard=next(t for t in ts if t['id']=='sample-wizard');s={k:int(v,16) for k,v in wizard['symbols'].items()}
 def read(at,size):
  for base,raw in mem:
   if base<=at and at+size<=base+len(raw):return raw[at-base:at-base+size]
  return img[at-0x40000400:at-0x40000400+size]
 table=int.from_bytes(read(0x4005a4f4,4),'big');old_desc=read(table+62*56,56);new_desc=read(table+52*56,56)
 assert struct.unpack_from('>I',old_desc,4)[0]==12 and struct.unpack_from('>I',old_desc,12)[0]==256
 assert struct.unpack_from('>I',new_desc,4)[0]==12 and struct.unpack_from('>I',new_desc,12)[0]==32512
 patches=[]
 def change(at,old,new):
  assert read(at,len(old))==old,(hex(at),read(at,len(old)).hex(),old.hex())
  assert len(old)==len(new);patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 def find(symbol,size,old,new):
  raw=read(s[symbol],size);assert raw.count(old)==1,(symbol,raw.count(old))
  change(s[symbol]+raw.index(old),old,new)
 find('sampler_pre',512,bytes.fromhex('723e21410014'),bytes.fromhex('723421410014'))
 find('fine_hook',32,bytes.fromhex('0c800000003e'),bytes.fromhex('0c8000000034'))
 find('wf_popup',48,bytes.fromhex('0c800000003e'),bytes.fromhex('0c8000000034'))
 change(s['sampler_lfo_ids']+4,struct.pack('>I',62),struct.pack('>I',52))
 # Le formatter et le dessin fins sont attaches au record UI de l'ancien ID.
 # Deplacer leurs six operandes avec l'ID, sans toucher au record RC Type.
 start=s['apply_names'];span=read(start,s['fine_draw']-start)
 for address,count in ((0x40a72fac,1),(0x40a72fbc,1),(0x40a72fb0,1),(0x40a72fb4,1),(0x40a72fb8,2)):
  old=struct.pack('>I',address);assert span.count(old)==count,(hex(address),span.count(old))
  offset=0
  for _ in range(count):
   offset=span.index(old,offset);change(start+offset,old,struct.pack('>I',address-1000));offset+=4
 for key in ('name_swap','gran_swap','strch_swap','pluck_swap','wave_swap','lofi_swap','tv_swap'):
  at=s[key]+28;change(at,struct.pack('>I',62*56),struct.pack('>I',52*56))
  # Restaurer les vrais noms909 apres sortie de Wizard, pas les noms stock.
  change(at+16,read(at+16,12),new_desc[44:56])
 return dict(patches=patches,old_descriptor=62,new_descriptor=52,slot=12,range=[0,32512],diagnostics=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',default='build/909-preview/all');p.add_argument('--check',action='store_true');a=p.parse_args();data=make_data(a.case)
 target=ROOT/'docs/flasher-909-wizard-end-test';temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else target;out.mkdir(exist_ok=True)
 for f in (ROOT/'docs/flasher-supermodel-909').iterdir():
  if f.is_file() and f.suffix!='.wav':shutil.copyfile(f,out/f.name)
 for name in ('beat-diagnostic-data.js','beat-diagnostic.js'):shutil.copyfile(ROOT/'docs/flasher-machine-combinations-test'/name,out/name)
 shutil.copyfile(ROOT/'tools/web/model909/wizard-end.js',out/'909-wizard-end.js')
 (out/'909-wizard-end-data.js').write_text('window.MC909WizardEnd='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf-8')
 text=(out/'index.html').read_text(encoding='utf-8');text=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,text);text=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",text);text=text.replace('window.MC909Released=true','window.MC909Released=false')
 notice='<p role="note"><strong data-l="en">909 Sample Wizard End range test.</strong><strong data-l="fr">Test plage End de Sample Wizard909.</strong> <span data-l="en">Sample End should move through its full range, including in Slice mode. Check the Slice editor too. The 909 RC Type control keeps its two positions. CPU/CUT diagnostics are enabled: hold TRACK + RETRIG and release. Released main and 909 flashers are unchanged.</span><span data-l="fr">Sample End doit parcourir sa plage complete, mode Slice compris. Verifier aussi l editeur de slices. RC Type909 conserve ses deux positions. Diagnostics CPU/CUT actifs : tenir TRACK + RETRIG puis relacher. Versions principales et909 publiees inchangees.</span></p>'
 text=text.replace('<main class="wrap fl">','<main class="wrap fl">'+notice).replace('909-release.js?','test-release.js?')
 text=text.replace('</body>',''.join(f'<script src="{name}?v={STAMP}"></script>' for name in ('beat-diagnostic-data.js','beat-diagnostic.js','909-wizard-end-data.js','909-wizard-end.js'))+'</body>');(out/'index.html').write_text(text,encoding='utf-8')
 (out/'test-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='909-Wizard-End-test.1',date='2026-10-18',changes=[dict(en='Sample Wizard End uses its full range without changing the binary 909 RC Type control. Test with diagnostics; hardware verification pending.',fr='Sample Wizard End retrouve sa plage complete sans modifier RC Type909 binaire. Test avec diagnostics ; verification materielle attendue.')])])+';\n',encoding='utf-8')
 (out/'BUILD.json').write_text(json.dumps(dict(stamp=STAMP,scope='test-only',base='909.7',diagnostics=True,hardware_verified=False,released_flashers_unchanged=True),indent=2)+'\n')
 for name in ('quick-reference.md','quick-reference-fr.md'):
  f=out/name;f.write_text(f.read_text(encoding='utf-8').rstrip()+'\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 print('PASS test909 End : references Wizard seules, DSP et descripteurs909 conserves')
if __name__=='__main__':main()
