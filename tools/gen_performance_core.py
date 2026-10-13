#!/usr/bin/env python3
"""Noyau performance autonome : slide/Scale Lock MIT, sans sampler ; note65.

--cycles SYX --model-tg CLONE --output JSON [--check]. Aucun catalogue existant
modifié. Modules sélectionnés dans la source MIT au commit épinglé.
"""
import argparse,hashlib,json,pathlib,struct,subprocess,tempfile,shutil
import build
from gen_model_tg import MODEL_TG_COMMIT,git
from gen_seq_gen import symbols,main_os_from_syx,STOCK
ROOT=pathlib.Path(__file__).resolve().parents[1]
START=0x401ab750
EXPORTS=('boot_extra_hook','key_hook','led_hook','core_pre','core_audio_end','snap_note','scale_state','key_state','set_held','mod_used','blk_clk','mm_obj','rtg_on','sle_on','show_popup','SLD_BASE','sld_init','sld_seq','sld_reset','sld_led','sld_apply','install_scale_menu_item','blob_start','reserved_end')
def source(repo):
 if git(repo,'rev-parse','HEAD')!=MODEL_TG_COMMIT:raise ValueError('Model-TG : commit non épinglé')
 if git(repo,'status','--porcelain'):raise ValueError('Model-TG : clone modifié')
 text=pathlib.Path(repo,'src/model_tg.s').read_text()
 def cut(start,end):return text[text.index(start):text.index(end,text.index(start))]
 parts=[cut('kh_mod:\n','kh_preset:\n'),cut('kh_slide:\n','kh_sle:\n').replace('bnew    kh_other','bnew    kh_out'),
        cut('SLIDE_BIT =','| ================= lo-fi'),cut('show_popup:\n','    .balign 4\npopup_mult:'),
        cut('snap_note:\n','| ---- browser: remember what was selected'),cut('scale_state:','    .balign 4\nfilt_mk:')]
 return '| Copyright (c) 2026 TinyGregAudio, MIT ; voir LICENSE-Model-TG.\nMAX_TRK=6\n'+ '\n'.join(parts)
def generate(stock,repo,cross=None):
 cross=cross or next((c for c in ("m68k-linux-gnu-","m68k-elf-") if shutil.which(c+"gcc") or shutil.which(c+"as")),"m68k-linux-gnu-")
 assert hashlib.sha256(stock).hexdigest()==STOCK
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);(p/'modules.s').write_text((ROOT/'tools/machines/performance_core/core.s').read_text()+'\n'+source(repo).replace('bnes    kh_eat','bnew    kh_eat'));objs=[]
  for name,path in (('modules',p/'modules.s'),):
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(path)],check=True)
  def link(end):
   subprocess.run([cross+'ld','-Ttext='+hex(START),'--defsym=blob_start='+hex(START),'--defsym=reserved_end='+hex(end),'-e','boot_extra_hook','-o',str(p/'core.elf'),*objs],check=True)
   subprocess.run([cross+'objcopy','-O','binary',str(p/'core.elf'),str(p/'core.bin')],check=True)
   return (p/'core.bin').read_bytes()
  probe=link(START+16384);blocks=(len(probe)+16383)//16384;blob=link(START+blocks*16384);assert len(probe)==len(blob)
  syms=symbols(cross,p/'core.elf')
 writes=[]
 def put(va,data,old=None):
  prev=stock[va-build.BASE:va-build.BASE+len(data)]
  if old is not None:assert prev.hex()==old,(hex(va),prev.hex())
  writes.append({'off':va-build.BASE,'old':prev.hex(),'new':data.hex()})
 def jump(va,name,size=6,old=None):put(va,b'\x4e\xf9'+struct.pack('>I',syms[name])+b'\x4e\x71'*((size-6)//2),old)
 put(0x40000530,b'\x4e\xf9'+struct.pack('>I',syms['boot_extra_hook'])+b'\x4e\x71'*2,'4ebaff8041f9fc044000')
 put(0x400792f2,struct.pack('>I',0x401eb750+20*blocks),'401eb750')
 put(0x400792bc,struct.pack('>I',0x401eb750+20*(blocks+1)+16),'401eb774')
 jump(0x4007240c,'key_hook',6,'206f00042028')
 jump(0x400a7da8,'core_pre',8,'2d41003c4a936730')
 put(0x40059872,b'\x4e\xb9'+struct.pack('>I',syms['core_audio_end']),'4eb9400567ba')
 jump(0x400169f0,'sld_reset',8,'4feffff448d7040c')
 put(0x40021f56,b'\x4e\xb9'+struct.pack('>I',syms['sld_led'])+b'\x4e\x71'*8,'2f034e944879404a8cb82f0d2f002f024e964fef0014')
 for va,old in ((0x400551a6,'4ebaf7264fef0018'),(0x40055bfa,'4ebaecd24fef0018')):put(va,b'\x4e\xb9'+struct.pack('>I',syms['sld_seq'])+b'\x4e\x71',old)
 jump(0x4002f7d8,'install_scale_menu_item')
 jump(0x4008173c,'note_on_hook',6,'b083650001ce');jump(0x40081474,'note_off_hook',6,'b08365000178')
 for va in (0x400ff9b8,0x400ffa78,0x40103070,0x401031b4,0x40107e18):put(va,struct.pack('>I',syms['led_hook']),'400d7648')
 offset=START-(build.BASE+len(stock));assert offset>=0
 tweak={'id':'performance-core','order':30,'name':'Noyau performance — test sans Model-TG','description':['Slide trigs et Scale Lock extraits de Model-TG MIT, sans sampler. Latching mute et trig preview séparés. Expérimental.'],'device':'Model:Cycles','os':'1.13','section':3,'status':'experimental','conflicts':['model-tg','model-tg-st'],'requires':[],'writes':sorted(writes,key=lambda x:x['off']),'symbols':{k:hex(syms[k]) for k in EXPORTS},'append':{'at':hex(build.BASE+len(stock)),'dest':hex(build.BASE+len(stock)),'parts':[{'dest':hex(START),'hex':blob.hex()}],'reloc':[],'size':offset+len(blob)}}
 build.apply_writes(stock,[tweak])
 return tweak,blob,syms

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--model-tg',required=True);ap.add_argument('--output',required=True);ap.add_argument('--cross');ap.add_argument('--check',action='store_true');a=ap.parse_args()
 t,b,s=generate(main_os_from_syx(a.cycles),a.model_tg,a.cross);out=pathlib.Path(a.output);text=json.dumps(t,indent=1,ensure_ascii=False)+'\n'
 if a.check:assert out.read_text()==text
 else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
 print('ok : noyau autonome',len(b),'octets ; sampler absent ; réservé',hex(s['reserved_end']-START))
if __name__=='__main__':main()
