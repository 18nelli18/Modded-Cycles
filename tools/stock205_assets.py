"""Profil prive205 : six machines stock, pack non-machine204 conserve.
Les IDs absents restent des slots de securite muets, jamais des choix de menu.
"""
import json,struct,subprocess
CODE=0x46888000

def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 def read(at,n):
  area,base=(prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL)
  return bytes(area[at-base:at-base+n])
 def edit(at,new):
  area=prefix if at<RUNTIME else rt if at<TAIL else tail
  patch(at,read(at,len(new)),new,area)
 def jump(at,to):edit(at,b'\x4e\xf9'+struct.pack('>I',to))
 fx=meta['fx_menu']['symbols'];sy=meta['tiny_extra']['symbols']
 c='''typedef unsigned int u32;typedef int s32;
const char st_name[]="UNAVAILABLE",st_label[]="---";
extern volatile u32 machine_valid,machine_stamp,machine_result;
u32 st_step(u32 machine,s32 d){if(machine>5)machine=0;if(d>0&&machine<5)machine++;if(d<0&&machine)machine--;return machine;}
u32 st_fx_step(u32 machine,s32 d){if(!d)return machine<6?machine:0;u32 now=*(volatile u32*)0xfc07000c;if(machine_valid&&machine==machine_result&&now-machine_stamp<5406720u)return machine;machine_result=st_step(machine,d);machine_valid=1;machine_stamp=now;return machine_result;}
u32 st_noop(void){return 0;}
u32 st_unchanged(u32 x){return x;}
void st_update(s32 m,char*v,const char*p){}
void st_render(s32*out,char*v){for(u32 i=0;i<32;i++)out[i]=0;}
'''
 asm='''.text
.globl st_increment,st_marks,st_dispatch
st_dispatch:
 cmpi.l #6,%d4
 bcs.s 4f
 movea.l %d3,%a0
 moveq #31,%d0
5: clr.l (%a0)+
 subq.l #1,%d0
 bpl.s 5b
 jmp 0x400a7e24
4: cmp.l %d4,%d0
 bcs.s 6f
 jmp 0x46788700
6: jmp 0x400a7e24
st_increment:
 lea -8(%sp),%sp
 movem.l %a0-%a1,(%sp)
 move.l %d5,-(%sp)
 move.l %d0,-(%sp)
 jsr st_step
 addq.l #8,%sp
 movem.l (%sp),%a0-%a1
 addq.l #8,%sp
 moveq #-1,%d1
 jmp 0x400148bc
st_marks:
 lea 0x40070c4e,%a2
 lea 0x40070efc,%a3
 clr.l %d5
1: move.l %d5,%d0
 mulu.w #9,%d0
 add.l #68,%d0
 pea 1
 pea 13
 move.l %d0,-(%sp)
 pea 9
 subq.l #4,%d0
 move.l %d0,-(%sp)
 move.l %d2,-(%sp)
 cmp.l %d5,%d3
 bne.s 2f
 jsr (%a3)
 bra.s 3f
2: jsr (%a2)
3: lea 24(%sp),%sp
 addq.l #1,%d5
 cmpi.l #6,%d5
 bne.s 1b
 jmp 0x400a26f2
'''
 (build/'stock205.c').write_text(c);(build/'stock205.S').write_text(asm)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objs=[]
 for ext in ('c','S'):
  obj=build/('stock205_'+ext+'.o');subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-c',str(build/('stock205.'+ext)),'-o',str(obj)],check=True);objs.append(str(obj))
 elf=build/'stock205.elf';binary=build/'stock205.bin';args=[cross+'ld.exe','-e','st_increment','-Ttext',hex(CODE)]
 for k in ('machine_valid','machine_stamp','machine_result'):args+=['--defsym',k+'='+hex(fx[k])]
 subprocess.run(args+['-o',str(elf)]+objs,check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
 symbols={v[2]:int(v[0],16) for l in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=l.split())==3};blob=binary.read_bytes();assert CODE+len(blob)<0x46889000
 # Restaurer les chaines communes avant de supprimer les intercepteurs Estus.
 es=meta['estus']['symbols']
 def restore(at,tramp):
  raw=read(tramp,32)
  for n in range(6,24,2):
   if raw[n:n+6]==b'\x4e\xf9'+struct.pack('>I',at+n):
    assert read(at,2)==b'\x4e\xf9';edit(at,raw[:n]);return
  raise AssertionError(('trampoline',hex(at),hex(tramp),raw.hex()))
 restore(meta['four_lfos']['symbols']['mx_frame'],es['lxr178_ui_old'])
 restore(fx['fx_encoder'],es['estus_old_encoder'])
 restore(0x400a7ab8,es['lxr178_old_reset'])
 edit(0x401005bc,struct.pack('>I',es['lxr178_previous_popup']))
 # Hooks importeurs/moteurs : retour aux prologues natifs gardes.
 for at,new in [(0x4007f694,'487940f1bf24'),(0x4007f6a8,'4fefffd848d77c7c'),(0x400a6d5c,'4e56ff8c48d73cfc')]:
  assert read(at,2)==b'\x4e\xf9';edit(at,bytes.fromhex(new))
 ws=meta['wizard_display'];assert read(ws['hook'],2)==b'\x4e\xf9';edit(ws['hook'],bytes.fromhex(ws['old']))
 # Effacer les plages exclusives. Les trous SRAM conservent les aides communes
 # et la copie native CHORD du bootstrap reste en place.
 ranges=[]
 def erase(lo,hi,label):
  assert lo<hi and not any(a<hi and lo<b for a,b,_ in ranges),(hex(lo),hex(hi),label)
  ranges.append((lo,hi,label));edit(lo,bytes(hi-lo))
 profile=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());selection=next(t for t in profile['composedTweaks'] if t['id'].startswith('machine-selection'))
 for i,p in enumerate(selection['append']['parts']):
  if 'syntakt' in p:
   lo=int(p['dest'],16);a,b=map(lambda s:int(s,16),p['syntakt']);erase(lo,lo+b-a,'Syntakt'+str(i))
 for lo,hi,label in [(0x46731000,0x46731144,'Syntakt bridge'),(0x46742000,0x46784000,'MACRO/ACID/WAVE/TINY'),(0x46785000,0x46788000,'old RETROSYN'),(meta['shadow']['code'],meta['shadow']['end'],'Shadow'),(meta['feral']['code'],meta['feral']['end'],'Feral'),(meta['junior']['code'],meta['junior']['code']+meta['junior']['code_bytes'],'ELDER'),(meta['feral_playable']['code'],meta['feral_playable']['code']+meta['feral_playable']['code_bytes'],'Feral wrapper'),(meta['speak']['code'],meta['speak']['end'],'SPEAK'),(0x46840000,meta['fundamentals']['symbols']['bf_active'],'ACID DSP'),(meta['fundamentals']['symbols']['acid_gain_render'],meta['fundamentals']['symbols']['fund_code_end'],'ACID tables/gain'),(meta['wave_starter']['code'],meta['wave_starter']['code']+meta['wave_starter']['code_bytes'],'WAVE browser'),(meta['wave_starter']['data'],meta['wave_starter']['end'],'WAVE PCM'),(meta['legacy']['code'],meta['legacy']['code']+meta['legacy']['code_bytes'],'LEGACY DSP/bank'),(0x46888000,0x46889000,'LEGACY art'),(meta['punch']['code'],meta['punch']['code']+meta['punch']['code_bytes'],'PUNCH'),(meta['private_retrosyn']['code'],meta['private_retrosyn']['code']+meta['private_retrosyn']['code_bytes'],'RETROSYN'),(meta['wizard_display']['code'],meta['wizard_display']['code_end'],'Wizard display')]:erase(lo,hi,label)
 for p in meta['estus']['segments']:erase(p['at'],p['at']+p['bytes'],'ESTUS')
 # Les anciennes destinations deja mises en cache sont des passerelles sures.
 stubs={}
 def stub(at,to):
  if not any(a<=at and at+6<=b for a,b,_ in ranges):return
  jump(at,to);stubs[at]=to
 for key in ('speak','legacy','punch','private_retrosyn','junior','shadow'):
  for name,at in meta[key].get('symbols',{}).items():
   if name in ('dx7_popup','speak_popup'):stub(at,fx['fx_popup'])
   elif name in ('punch_turn',):stub(at,symbols['st_unchanged'])
   elif name in ('dx7_service','dx7_browser_key','dx7_browser_encoder','dx7_browser_draw','dx7_status_draw','dx7_library_load','dx7_library_save','wave_browser_key'):stub(at,symbols['st_noop'])
 for key in ('feral','tiny_extra'):
  for name in ('update','render'):
   if name in meta[key]:stub(meta[key][name],symbols['st_'+name])
 # Table native25 cases : 6 seulement installes, 19 gardes pour anciens fichiers.
 for machine in range(6,25):
  for row,target in ((0,'st_name'),(1,'st_update'),(2,'st_render')):
   at=0x4683c000+100*row+4*machine;previous=int.from_bytes(read(at,4),'big')
   if row:stub(previous,symbols[target])
   edit(at,struct.pack('>I',symbols[target]))
  edit(0x4683c000+300+4*machine,struct.pack('>I',1))
 for d in range(76,166):
  for off in (8,12,16):edit(0x4683c800+56*d+off,bytes(4))
  for off in (44,52):edit(0x4683c800+56*d+off,struct.pack('>I',symbols['st_label']))
 # Ancien registre conserve par le bootstrap : plus aucune voix supplementaire.
 for machine in range(6,18):
  for row,target in ((0,'st_name'),(1,'st_update'),(2,'st_render')):edit(0x46789000+72*row+4*machine,struct.pack('>I',symbols[target]))
 # Les limites natives incluent chargement de son, lock de machine et menu.
 for at,reg in [(0x400a7dba,0x72),(0x400a7df4,0x70),(0x400147a4,0x70),(0x400a25e0,0x70)]:
  assert read(at,2)==bytes([reg,24]);edit(at,bytes([reg,5]))
 assert read(0x467886fa,6)==bytes.fromhex('b08465000084');jump(0x467886fa,symbols['st_dispatch'])
 jump(fx['fx_machine_step'],symbols['st_fx_step']);jump(sy['tiny_menu_increment'],symbols['st_increment']);jump(sy['marks'],symbols['st_marks'])
 # Pas de navigateur WAVE/LEGACY ni de moteur MIDI via un son sauvegarde.
 # L'audio et les E/S MIDI ordinaires partagent leurs enveloppes de routage.
 edit(CODE,blob)
 meta['tiny_extra']['menu_order']=list(range(6));meta['tiny_extra']['installed_machine_count']=6
 return dict(code=CODE,code_bytes=len(blob),symbols=symbols,visible_order=list(range(6)),removed_ids=list(range(6,25)),machine_names=['Kick','Snare','Metal','Perc','Tone','Chord'],erased_ranges=[dict(lo=a,hi=b,label=c) for a,b,c in ranges],safe_stubs={hex(k):hex(v) for k,v in stubs.items()},stable_ids=True,retains_all_non_machine_features=True,hardware_tested=False)
