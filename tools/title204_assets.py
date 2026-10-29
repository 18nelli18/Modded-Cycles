"""Titre SUPERMODEL versionne ; meme animation et contrat natif, aucune API OS alteree."""
import json,subprocess,hashlib,re
from pathlib import Path

def flasher_release(root):
 # Le checkout de publication peut etre distinct du source de developpement.
 candidates={root/'docs/flasher/BUILD.json',Path.cwd()/'docs/flasher/BUILD.json'}
 for parent in {root.parent,Path.cwd()}:
  candidates.update(parent.glob('publish-*/docs/flasher/BUILD.json'))
 found=[]
 for p in candidates:
  if not p.exists():continue
  m=json.loads(p.read_text(encoding='utf-8-sig'));v=str(m.get('release',''))
  if re.fullmatch(r'\d+\.\d+(?:\.\d+)?',v) and m.get('release_approved_by'):
   found.append((tuple(map(int,v.split('.'))),v,str(p)))
 assert found,'Version du flasher introuvable : fournir --title-version'
 _,version,path=max(found)
 return version,path

def apply(root,build,prefix,patch,version,lite=False,previous=None):
 from gen_governor_recovery_test import BASE
 import gen_boot_supermodel as G
 assert re.fullmatch(r'v?\d+(?:\.\d+)*',version),version
 digits={
 '1':['00100','01100','00100','00100','00100','00100','01110'],
 '2':['01110','10001','00001','00010','00100','01000','11111'],
 '3':['11110','00001','00001','01110','00001','00001','11110'],
 '4':['00010','00110','01010','10010','11111','00010','00010'],
 '5':['11111','10000','10000','11110','00001','00001','11110'],
 '6':['01110','10000','10000','11110','10001','10001','01110'],
 '7':['11111','00001','00010','00100','01000','01000','01000'],
 '8':['01110','10001','10001','01110','10001','10001','01110'],
 '-':['00000','00000','00000','11111','00000','00000','00000']}
 G.FONT.update(digits);edition=('LITE ' if lite else '')+version.upper();ec,ee=G.columns(edition,1)
 consts=dict(NF=G.NF,TITLE_X=G.TITLE_X,TITLE_Y=G.TITLE_Y,TITLE_H=G.TITLE_H,TITLE_START=G.TITLE_START,TITLE_COUNT=len(G.TITLE),TITLE_WIDTH=len(G.TC),LINE_START=G.LINE_START,LINE_Y=G.LINE_Y,CREDIT_X=G.CREDIT_X,CREDIT_Y=G.CREDIT_Y,CREDIT_H=G.CREDIT_H,CREDIT_START=G.CREDIT_START,CREDIT_COUNT=len(G.CREDIT),EDITION_ENABLED=1,EDITION_X=(128-len(ec))//2,EDITION_Y=54,EDITION_H=7,EDITION_START=56,EDITION_COUNT=len(edition))
 assert len(ec)<=118 and 56+2*(len(edition)-1)<G.NF
 (build/'supermodel.inc').write_text(''.join(f'.equ {k},{v}\n' for k,v in consts.items()))
 data=''
 for name,cols,ends in (('title',G.TC,G.TE),('credit',G.CC,G.CE),('edition',ec,ee)):
  data+=name+'_ends: .byte '+','.join(map(str,ends))+'\n.balign 2\n'+name+'_cols: .word '+','.join(map(str,cols))+'\n'
 (build/'supermodel_data.inc').write_text(data)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');obj=build/'title204.o';elf=build/'title204.elf';binary=build/'title204.bin'
 subprocess.run([cross+'as.exe','-march=cfv4e','-I',str(build),str(root/'tools/machines/boot_supermodel/boot_supermodel.S'),'-o',str(obj)],check=True)
 subprocess.run([cross+'ld.exe','-T',str(root/'tools/machines/boot_anim/boot_anim.ld'),'--no-warn-rwx-segments','-o',str(elf),str(obj)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.anim',str(elf),str(binary)],check=True);code=binary.read_bytes();assert len(code)<=G.BODY_END-G.BODY,(len(code),G.BODY_END-G.BODY)
 if previous is None:
  profile=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());entry=next(t for t in profile['composedTweaks'] if t['id']=='supermodel-startup')['writes'][0];old=bytes.fromhex(entry['new']);assert entry['off']==G.BODY-BASE and prefix[G.BODY-BASE:G.BODY-BASE+len(old)]==old
 else:
  assert previous['code']==G.BODY
  old=bytes(prefix[G.BODY-BASE:G.BODY-BASE+previous['code_bytes']])
  assert hashlib.sha256(old).hexdigest()==previous['sha256'],'Ancien titre non conforme aux metadonnees'
 patch(G.BODY,bytes(prefix[G.BODY-BASE:G.BODY-BASE+len(code)]),code,prefix)
 return dict(name='Supermodel Lite' if lite else 'Supermodel',version=version,edition=edition,code=G.BODY,code_bytes=len(code),sha256=hashlib.sha256(code).hexdigest(),native_os_protocol_version_unchanged=True,hardware_tested=False)
