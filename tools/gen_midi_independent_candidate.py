#!/usr/bin/env python3
"""Candidat Banque indépendant : hooks natifs et payload privé commun, sans stockage.

Sortie locale uniquement ; aucune inscription au catalogue avant preuves natives.
"""
import argparse,json,pathlib,struct
import build,sprites,aplib_dense,copy
from chord_keys_pr87 import load_stock

def generate(stock,data,engine=None):
 sampler=data.get('sampler',False)
 core=dict(data['core']);
 if not sampler:core.pop('append')
 core['writes']=[dict(w) for w in core['writes']]
 start=int(data['start'],16);syms={k:int(v,16) for k,v in data['symbols'].items()}
 origin=int(core['symbols']['blob_start'],16)
 code=bytes.fromhex(data['core']['append']['parts'][0]['hex'])
 raw=bytes.fromhex(data['raw']) if sampler else code+bytes(start-origin-len(code))+bytes.fromhex(data['raw'])
 extra=data.get('extra_runtime')
 if extra:
  at=int(extra['parts'][0]['dest'],16);piece=bytes.fromhex(extra['parts'][0]['hex']);raw_origin=start if sampler else origin
  assert at>=raw_origin+len(raw)
  raw=bytearray(raw+bytes(at-raw_origin-len(raw))+piece);end=raw_origin+len(raw)
  off=syms['ml_boot_skip']-raw_origin
  assert raw[off:off+6]==b'\x20\x7c'+struct.pack('>I',syms['ML_BANK_END'])
  raw[off+2:off+6]=struct.pack('>I',end);raw=bytes(raw)
  syms.update({k:int(v,16) for k,v in extra['symbols'].items()});syms['ML_BANK_END']=end
 packed=aplib_dense.pack(raw,depth=128)
 loader=int(data['loader'],16);stub=bytes.fromhex(data['stub'])
 target=b'\x43\xf9'+struct.pack('>I',start)
 assert stub.count(target)==1
 if not sampler:stub=stub.replace(target,b'\x43\xf9'+struct.pack('>I',origin))
 # Le bootstrap du noyau ne doit pas être appelé avant décompression.
 if not sampler:core['writes']=[w for w in core['writes'] if w['off']!=0x40000530-build.BASE]
 supports=copy.deepcopy(data.get('supports',[]))
 if extra:supports.append(dict(id='chord-keys-supermodel',order=45,status='experimental',section=3,writes=extra['writes'],symbols=extra['symbols'],requires=[],conflicts=[]))
 base,_=build.apply_writes(stock,([engine] if engine else [])+[core]+supports);writes=[]
 def put(at,new,expected=None):
  old=base[at-build.BASE:at-build.BASE+len(new)]
  assert len(old)==len(new),(hex(at),len(old),len(new))
  if expected:assert old.hex()==expected,(hex(at),old.hex(),expected)
  writes.append(dict(off=at-build.BASE,old=old.hex(),new=new.hex()))
 def jump(at,name,n=6,call=False,expected=None):
  put(at,(b'\x4e\xb9' if call else b'\x4e\xf9')+struct.pack('>I',syms[name])+b'\x4e\x71'*((n-6)//2),expected)
 if engine:
  expected=b'\x4e\xf9'+struct.pack('>I',int(core['symbols']['boot_extra_hook'],16)) if sampler else bytes.fromhex('4feffff048d700f04ef9400004ba');hits=[]
  for w in engine['writes']:
   body=bytes.fromhex(w['new'])
   for i in range(0,len(body)-len(expected)+1,2):
    if body[i:i+len(expected)]==expected:hits.append(build.BASE+w['off']+i)
  assert len(hits)==1,('reprise moteur ambiguë',hits)
  put(hits[0],b'\x4e\xf9'+struct.pack('>I',loader)+b'\x4e\x71'*((len(expected)-6)//2),expected.hex())
 elif sampler:put(0x40000532,struct.pack('>I',loader),core['symbols']['boot_extra_hook'][2:])
 else:put(0x40000530,b'\x4e\xf9'+struct.pack('>I',loader)+b'\x4e\x71'*2,'4ebaff8041f9fc044000')
 blocks=(start-origin+len(raw)+16383)//16384 if sampler else (len(raw)+16383)//16384
 for at,val in [(0x400792f2,0x401eb750+20*blocks),(0x400792bc,0x401eb750+20*(blocks+1)+16)]:put(at,struct.pack('>I',val))
 for at,body in [(loader,stub)]+[(int(at,16),bytes.fromhex(body)) for at,body in data['fragments']]:
  red=sprites.redirect_write(at);put(build.BASE+red['off'],bytes.fromhex(red['new']));put(at,body)
 for at,name,n,call,expected in [
  (0x4006a660,'ml_repeat_project_hook',8,False,'4cd7040c4fef0020'),
  (0x4008e8c4,'mlp_pulse_guard',10,False,'202f000441f94010abf8'),
  (0x400012cc,'mm_rx',6,False,'2f02242f0008'),
  (0x400597c6,'mlcc_audio',6,True,None),
  (0x4007240c,'ml_key',6,False,None),
  (0x40054686,'ml_start_hook',6,False,None),
  (0x400594a8,'ml_audio_hook',6,True,None),
  (0x40006a4a,'ml_ui_hook',8,False,None),
  (0x4001c5da,'ml_settings_toggle',6,True,'4eb940077da8'),
  (0x4001b28a,'mlp_stock_track',6,True,'4eb940012412'),
  (0x4001b774,'mlp_stock_volume',6,True,'4eb940009c5a'),
  (0x4001b722,'mlp_stock_pan',6,True,'2068001c4e90'),
  (0x4001b6ba,'mlp_stock_track_label',10,False,'486a0001283c401117e0')]:jump(at,name,n,call,expected)
 if data.get('genie'):
  sg=next(t for t in supports if t['id']=='scale-gen-st-queued')['symbols']
  for native,ours in [('sg_action_generate','ml_genie_generate'),('sg_action_undo','ml_genie_undo')]:
   target=b'\x4e\xb9'+struct.pack('>I',int(sg[native],16));menu=int(sg['sg_menu_key'],16)
   sites=[at for at in range(menu,menu+0x400,2) if base[at-build.BASE:at-build.BASE+6]==target]
   assert len(sites)==1,(native,sites)
   put(sites[0],b'\x4e\xb9'+struct.pack('>I',syms[ours]))
  for native,ours in [('sg_pad','ml_genie_pad'),('sg_menu_key','ml_genie_menu_key'),('sg_render','sg_render')]:
   target=b'\x20\x3c'+struct.pack('>I',int(sg[native],16))
   sites=[build.BASE+i for i in range(0,len(base)-5,2) if base[i:i+6]==target]
   assert len(sites)==1,(native,sites)
   put(sites[0],b'\x20\x3c'+struct.pack('>I',syms[ours]))
  target=b'\x4e\xb9'+struct.pack('>I',0x4007700e)
  sites=[at for at in range(int(sg['sg_o_allocate'],16),int(sg['sg_o_done'],16),2) if base[at-build.BASE:at-build.BASE+6]==target]
  assert len(sites)==1,sites
  put(sites[0],b'\x4e\xb9'+struct.pack('>I',syms['ml_genie_present']))
 source=0x401f8f76
 assert source+len(packed)<=build.END_LIMIT
 tweak=dict(id='midi-bank-independent',order=60,status='experimental',section=3,requires=[core['id']]+[t['id'] for t in supports],conflicts=[],writes=sorted(writes,key=lambda w:w['off']),symbols={k:hex(v) for k,v in syms.items()},append=dict(at=hex(source),dest=hex(start if sampler else origin),size=len(raw),parts=[dict(dest=hex(start if sampler else origin),hex=raw.hex())],reloc=[],compress='aplib',compressed_hex=packed.hex(),zero_pad_from=hex(int(core['append']['at'],16)+core['append']['size'] if sampler else build.BASE+len(stock))),prototype_only=True,flashable=False,cache_blocks=blocks,pending=['native_boot_input_audio_midi_proofs','optional_feature_profiles','hardware_test'])
 build.apply_writes(stock,([engine] if engine else [])+[core]+supports+[tweak])
 return dict(core=core,bank=tweak,supports=supports,**({'engine':engine} if engine else {}))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--compiled',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');p.add_argument('--engine');p.add_argument('--catalog');a=p.parse_args()
 engine=next(t for t in json.loads(pathlib.Path(a.catalog).read_text()) if t['id']==a.engine) if a.engine else None
 out=generate(load_stock(a.cycles),json.loads(pathlib.Path(a.compiled).read_text()),engine);text=json.dumps(out,indent=1,ensure_ascii=False)+'\n';path=pathlib.Path(a.output)
 if a.check:assert path.read_text()==text
 else:path.write_text(text)
 print('ok : hooks vérifiés sur OS stock ;',out['bank']['cache_blocks'],'blocs privés ; candidat non flashable')
if __name__=='__main__':main()
