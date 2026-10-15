"""Fusion privée des hooks WAVE/Wizard : un propriétaire par site natif.

La sélection et les fichiers restent distincts, l'identité Transfer et le
message de chargement sont communs ; aucun hook Model-TG global installé.
"""
import json,pathlib,struct,copy,hashlib
import build,ref_mainos
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/sample-wizard-main');stock=load_stock('firmware/model-cycles_OS1.13.syx')
wizard=json.load(open(P/'installer.json'));eng=json.load(open(P/'engine-all.json'));wave=json.load(open(P/'wave.json'));writes=json.load(open(P/'wave-writes.json'))
s={k:int(v,16) for k,v in wizard['symbols'].items()};g=wave['gsyms']
# Le code WAVE est notre glue MIT : seuls ses pointeurs absolus sont partagés.
replacements={g['wt_msg']:s['msg_buf'],g['smp_mode']:s['id_mode']};counts={k:0 for k in replacements}
for part in eng['append']['parts']:
 if 'hex' not in part:continue
 at=int(part['dest'],16)
 if not any(at==p[0] for p in wave['blobs']):continue
 b=bytearray.fromhex(part['hex'])
 for off in range(0,len(b)-3,2):
  value=int.from_bytes(b[off:off+4],'big')
  if value in replacements:b[off:off+4]=struct.pack('>I',replacements[value]);counts[value]+=1
 part['hex']=b.hex()
assert g['wt_msg']==s['msg_buf'] and g['smp_mode']==s['id_mode'], 'glue non partagée'
raw=bytearray.fromhex(wizard['append']['parts'][0]['hex']);base=int(wizard['append']['dest'],16)
for sym,value in [('av_wave_tick',g['wt_tick']),('av_wave_note',g['wt_note']),('av_wave_yes',g['wt_yes']),('av_wave_machine',14)]:struct.pack_into('>I',raw,s[sym]-base,value)
wizard['append']['parts'][0]['hex']=raw.hex()
# Les destinations moteurs remplacent les tables Wizard ; l'installateur ne
# garde que les hooks qui ne chevauchent pas leurs versions à quinze machines.
def span(w):return (w['off'],w['off']+len(w['new'])//2)
def intersects(a,b):return a[0]<b[1] and b[0]<a[1]
engine_spans=[span(w) for w in eng['writes']]
removed=[]
owned=[span(w) for w in wizard['writes']]+engine_spans
shared=[]
for w in writes:
 if any(intersects(span(w),r) for r in owned):shared.append(hex(w['off']+build.BASE))
 else:eng['writes'].append(w)
# Les générateurs produisent des surcouches avec old du fournisseur. Appliquer
# ces gardes avant d'aplatir conserve les octets hors d'une écriture partielle
# (p.ex. adresse d'un JSR, sans perdre son opcode).
merged,_=build.apply_writes(stock,[wizard,eng]);intervals=[]
for lo,hi in sorted(span(w) for w in wizard['writes']+eng['writes']):
 if intervals and lo<=intervals[-1][1]:intervals[-1][1]=max(hi,intervals[-1][1])
 else:intervals.append([lo,hi])
allwrites=[dict(off=lo,old=stock[lo:hi].hex(),new=merged[lo:hi].hex()) for lo,hi in intervals]
wizard['writes']=allwrites;eng['writes']=[]
for a,b in zip(allwrites,allwrites[1:]):assert span(a)[1]<=span(b)[0]
eng['requires']=['sample-wizard'];wizard.update(prototype_only=True,flashable=False)
image,_=build.apply_writes(stock,[wizard,eng]);payload,_=build.build_payload([wizard,eng],stock,'firmware/Syntakt_OS1.42.syx')
(P/'combined.json').write_text(json.dumps([wizard,eng]));(P/'shared-report.json').write_text(json.dumps(dict(replaced_installer=removed,shared_wave=shared,relocations={hex(k):v for k,v in counts.items()},image_sha=hashlib.sha256(image+payload).hexdigest()),indent=2))
print('PASS fusion stricte :',len(allwrites),'écritures sans chevauchement ; WAVE/Wizard partage identité, UI, note et YES ;',len(payload),'octets flash ajoutés')
