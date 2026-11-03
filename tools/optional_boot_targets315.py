"""Optional : ne jamais revenir dans le staging de boot efface apres copie.

Le predicat WAVE est copie467a9a90 ->401bf4d0. Son trampoline rejoue
CMP5 et doit reprendre a401bf4d6, pas a467a9a96. Aucun travail audio ajoute.
"""
from pathlib import Path
import argparse,hashlib,json,struct

def resident_target(address):
 return 0x401aa140+address-0x46794700 if 0x46794700<=address<0x467ab320 else address

def repair(patches):
 fixes=[]
 for patch in patches:
  raw=bytearray.fromhex(patch['new']);changed=False
  for i in range(0,len(raw)-5,2):
   if raw[i:i+2] not in (b'\x4e\xf9',b'\x4e\xb9'):continue
   old=int.from_bytes(raw[i+2:i+6],'big');new=resident_target(old)
   if new==old:continue
   assert old==0x467a9a96 and i>=6 and raw[i-6:i]==bytes.fromhex('0c8000000005'),('unreviewed staging continuation',hex(patch['at']+i),hex(old))
   raw[i+2:i+6]=struct.pack('>I',new);fixes.append(dict(site=patch['at']+i,old=old,new=new));changed=True
  if changed:patch['new']=raw.hex()
 return fixes

def main():
 p=argparse.ArgumentParser();p.add_argument('--docs',type=Path,required=True);p.add_argument('--backup',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();a.backup.mkdir(parents=True,exist_ok=True);rows=[]
 for name,global_name,key in [('recipe.js','MCOptionalRecipe','patches'),('machinedrum-data.js','MCOptionalMDData','clean_patches')]:
  path=a.docs/name;text=path.read_text(encoding='utf-8');data=json.loads(text.split('=',1)[1].strip().rstrip(';'));fixes=repair(data[key])
  if a.check:assert not fixes,(name,fixes)
  elif fixes:
   (a.backup/name).write_text(text,encoding='utf-8');data['boot_trampoline_relocations']=fixes
   path.write_text('window.'+global_name+'='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
  rows.append(dict(file=name,fixes=fixes))
 if not a.check:
  path=a.docs/'BUILD.json';data=json.loads(path.read_text(encoding='utf-8'));data['recipe_sha256']=hashlib.sha256((a.docs/'recipe.js').read_bytes()).hexdigest();data['optional_boot_continuation_fixed']=True;path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (a.backup/('check.json' if a.check else 'repair.json')).write_text(json.dumps(rows,indent=2)+'\n');print('PASS Optional/MD boot continuations',rows)

if __name__=='__main__':main()
