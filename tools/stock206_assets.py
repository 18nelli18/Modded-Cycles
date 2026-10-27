"""Lite206 : supprimer les dependances WAVE des services UI et les callbacks
metadata d'anciens moteurs. Les reprises stock sont gardees octet par octet.
"""
import struct,subprocess
CODE=0x46850000

def apply(root,build,prefix,rt,tail,meta,patch,connect_offset=False):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL,read as load
 from stock205_assets import apply as strip
 result=strip(root,build,prefix,rt,tail,meta,patch)
 def area(at):return (prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL)
 def read(at,n):a,b=area(at);return bytes(a[at-b:at-b+n])
 changes=[]
 def edit(at,new):
  a,b=area(at);old=read(at,len(new));patch(at,old,new,a);changes.append(dict(at=at,old=old.hex(),new=new.hex()))
 def jump(at,to):edit(at,b'\x4e\xf9'+struct.pack('>I',to))
 _,_,stock,_=load(root/'firmware/model-cycles_OS1.13.syx')
 c='''typedef unsigned int u32;
#define N(a) ((u32(*)())(a))
u32 st6_state_at(u32 slot){if(slot>=76)slot=0;return 0x40a71754+100*slot;}
u32 st6_state_connect(u32 slot,u32 owner){N(0x400ddf60)(st6_state_at(slot),owner,0x40a71500);return 0x40a71500;}
'''
 if connect_offset:c=c.replace('N(0x400ddf60)(st6_state_at(slot),owner,','N(0x400ddf60)(st6_state_at(slot)+20,owner,')
 asm='''.text
.globl st6_idle
/* Callback de service sans retour : conserver tous les registres et le CCR. */
st6_idle:
 rts
'''
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objs=[]
 for ext,src in [('c',c),('S',asm)]:
  p=build/('stock206.'+ext);p.write_text(src);o=build/('stock206_'+ext+'.o');subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-c',str(p),'-o',str(o)],check=True);objs.append(str(o))
 elf=build/'stock206.elf';binary=build/'stock206.bin';subprocess.run([cross+'ld.exe','-e','st6_idle','-Ttext',hex(CODE),'-o',str(elf),*objs],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};blob=binary.read_bytes();assert len(blob)<0x400
 # Les trois callbacks WAVE existent dans le ROM et dans sa copie residente.
 old=struct.pack('>3I',0x4677a996,0x4677a750,0x4677a79a);new=struct.pack('>3I',sy['st6_idle'],sy['st6_idle'],result['symbols']['st_noop']);callbacks=[]
 for a,b in [(prefix,BASE),(rt,RUNTIME)]:
  matches=[i for i in range(0,len(a)-len(old)+1,2) if a[i:i+len(old)]==old];assert len(matches)==(0 if a is prefix else 1),(hex(b),matches)
  for off in matches:edit(b+off,new);callbacks.append(b+off)
 # Plus aucun son ne doit entrer dans les branches de navigateur WAVE.
 pred=read(0x467a9a90,44);assert pred[:6]==bytes.fromhex('0c8000000005');preds=[]
 for a,b in [(prefix,BASE),(rt,RUNTIME)]:
  matches=[i for i in range(0,len(a)-len(pred)+1,2) if a[i:i+len(pred)]==pred];assert len(matches)==(0 if a is prefix else 1),(hex(b),'predicate',matches)
  for off in matches:edit(b+off,bytes.fromhex('70004e75'));preds.append(b+off)
 # Hooks natifs originaux, aucune reconstitution approximee de leur ABI.
 sites=[(0x4003fa52,10,0x4677ab02),(0x400a40e2,8,0x4677aaf0),(0x400a6602,6,0x4677a5c4),(0x400a6c20,8,0x4677aa4e),(0x400a6f9c,10,0x4677ab26),(0x400a70b0,6,0x4677ab4c)]
 for at,n,target in sites:
  old=read(at,6);assert old[:2] in (b'\x4e\xf9',b'\x4e\xb9') and int.from_bytes(old[2:6],'big')==target,(hex(at),old.hex())
  edit(at,stock[at-BASE:at-BASE+n])
 # Copie du setter : le meme appel natif que son point d'origine.
 at=0x40185d20;assert read(at,6)==b'\x4e\xb9'+struct.pack('>I',0x4677a5c4);edit(at,stock[0x400a6602-BASE:0x400a6608-BASE])
 # Le renderer ACID d'ancien gain n'est plus une destination, meme en cache.
 at=0x467b4112;assert read(at,6)==b'\x4e\xb9'+struct.pack('>I',0x46776404);edit(at,b'\x4e\xb9'+struct.pack('>I',result['symbols']['st_render']))
 # Les anciens wrappers de descripteur PUNCH sont remplaces par les etats stock.
 tiny=meta['tiny_extra'];state=tiny['symbols'];lo=state['state_at'];hi=tiny['code']+tiny['code_bytes'];assert lo<state['state_connect']<hi
 edit(lo,bytes(hi-lo));jump(state['state_at'],sy['st6_state_at']);jump(state['state_connect'],sy['st6_state_connect'])
 # L'ancienne correction SY BITS n'a plus d'utilisateur ni de service permanent.
 bf=meta['fundamentals']['symbols'];lo=meta['fundamentals']['code'];hi=bf['fund_code_end'];edit(lo,bytes(hi-lo))
 for at,to in result['safe_stubs'].items():
  at=int(at,16)
  if lo<=at<hi:jump(at,int(to,16))
 for name,target in [('bf_edit',bf['bf_native_edit']),('bf_popup',meta['fx_menu']['symbols']['fx_popup']),('bf_prepare',meta['fx_menu']['symbols']['fx_frame_prepare'])]:jump(bf[name],target)
 # Ancienne enveloppe gain WAVE : aucun appel ne peut atteindre son DSP efface.
 fxp=meta['fx_project']['symbols'];at=fxp['wave_gain_render'];raw=read(at,96);target=struct.pack('>I',0x467796fc);off=raw.index(b'\x4e\xb9'+target);edit(at+off+2,struct.pack('>I',result['symbols']['st_render']))
 edit(CODE,blob)
 result.update(native_state_connect_offset=20 if connect_offset else 0,service_cleanup=True,service_symbols=sy,service_code=CODE,service_code_bytes=len(blob),wave_callback_slots=callbacks,wave_predicates=preds,restored_stock_hooks=[dict(at=a,bytes=n) for a,n,t in sites],cleanup_patches=changes)
 return result
