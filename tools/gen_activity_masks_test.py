"""Prototype2.65 : PUNCH stock, masques LFO et voix Wizard independante du mix principal."""
from pathlib import Path
import argparse,hashlib,json,math,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x4691a000;BSS=0x4691f000;S=R/'tools/machines/acid'
def main():
 p=argparse.ArgumentParser()
 for k in ('source','metadata','cycles','output'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--check',action='store_true');p.add_argument('--emac-dsp',action='store_true');p.add_argument('--reverb-network-opt',action='store_true')
 a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest();raw=a.source.read_bytes();m=json.loads(a.metadata.read_text(encoding='utf-8'));assert sha(raw)==m['sha256'];assert m.get('acid_articulation',{}).get('arp_retrigger') and m['sha256']=='8d9d7df60e212c1c8e1848c0e3b2d015c8e9a2d91269efde5177431d4554e72f'
 assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
 _,_,stock,ops=read(a.cycles);info,pkg,image,_=read(a.source);image=bytearray(image);O=a.output;O.mkdir(parents=True,exist_ok=True)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 full='ae_mode' in m['per_track_fx']['symbols'];assert m['per_track_fx']['symbols']['lt_bss_end']<=CODE
 network_blob=b'';network=None
 if a.reverb_network_opt:
  assert a.emac_dsp
  from reverb_network_assets import prepare
  network_blob,network=prepare(R,O,m,run);network_blob+=bytes((-len(network_blob))&3)
 aliases={**m['direct_jump']['aliases'],**m['direct_jump']['symbols'],**m['acid_articulation']['symbols'],**m['per_track_fx']['symbols']};aliases['pp_native']=aliases['mf_old_voice_playability'];aliases.pop('pp_voice_loop');aliases.pop('li_dispatch')
 lfo=(R/'tools/machines/track_fx/lfo-direct.c').read_text(encoding='utf-8').replace('volatile u32 li_noapply,li_active_tracks[3];','extern volatile u32 li_noapply;volatile u32 li_active_tracks[3];')
 (O/'lfo.c').write_text(lfo)
 (O/'punch.c').write_text('#define PP_UNIQUE 1\n#define PP_REMOVE_LEGACY 1\n'+(R/'tools/machines/track_fx/voice-punch.c').read_text(encoding='utf-8'))
 (O/'wizard-usb.S').write_text('.text\n.globl am_wizard_usb\nam_wizard_usb:\n moveq #0,%d0\n move.b 0x40002ceb,%d0\n cmpi.l #0x38,%d0\n bne.s 1f\n move.l %d2,-(%sp)\n move.l %d1,%d2\n lsl.l #2,%d2\n jmp 0x401adbfc\n1: jmp 0x401adc3a\n')
 assert image[0x4000053a-BASE:0x40000542-BASE]==stock[0x4000053a-BASE:0x40000542-BASE]
 with (O/'wizard-usb.S').open('a') as f:f.write('.globl am_boot_finish\nam_boot_finish:\n lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)\n lea 0x401adbf6,%a1\n move.w #0x4ef9,(%a1)+\n move.l #am_wizard_usb,(%a1)\n movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp\n.byte '+','.join(map(str,stock[0x4000053a-BASE:0x40000542-BASE]))+'\n jmp 0x40000542\n')
 aliases.update(mb_old_key=m['acid_articulation']['symbols']['sg_key'],mb_old_encoder=m['acid_articulation']['symbols']['sg_encoder'],mb_old_draw=m['acid_articulation']['symbols']['sg_draw'],mb_old_edit=m['direct_jump']['symbols']['jp_edit'],mb_old_frame=m['acid_articulation']['symbols']['sg_frame'],mb_native_rotate=int.from_bytes(image[0x400a2714-BASE:0x400a2718-BASE],'big'))
 for name in ('machine-confirm.c','machine-confirm-menu.c'):(O/name).write_text((R/'tools/machines/track_fx'/name).read_text(encoding='utf-8'))
 view=(R/'tools/machines/direct_jump/global.S').read_text(encoding='utf-8').replace('mf_global_draw','mb_global_draw').replace('ae_global_edit','mb_edit').replace('gc_tree_row','mb_tree_row').replace('moveq #11,%d0','moveq #13,%d0')
 view=view.replace('    jsr mb_tree_row','    clrb %a0@(1004)\n    clrb %a0@(1088)\n    jsr mb_tree_row',1)
 view=view.replace('.Lallocator: .byte 0','.Lmac: .asciz "Mac"\n.Ljump: .asciz "JUMP"\n.Lallocator: .byte 0')
 at=view.index('.Lts_rows:');prefix,rows=view[:at+len('.Lts_rows:')],view[at+len('.Lts_rows:'):]
 entries=[line for line in rows.splitlines() if line.startswith('.long')];entries.insert(1,'.long 0,0,0,.Lmac,0,1,.Lts_label,0,0,0,0,0,0,1,mb_value,0,0,0,0,0,0');entries.append('.long 0,0,0,.Ljump,0,1,.Lts_label,0,0,0,0,0,0,1,jp_value,0,0,0,0,0,0')
 callbacks='typedef unsigned int u32;extern volatile u32 gc_tree_cursor;\n'
 for i,line in enumerate(entries):
  fields=line.split(',');fn=fields[14];wrapper='mb_callback'+str(i);fields[14]=wrapper;entries[i]=','.join(fields)
  callbacks+=f'extern void {fn}(u32,u32,u32,u32,u32);void {wrapper}(u32 a,u32 b,u32 c,u32 x,u32 y){{u32 saved=gc_tree_cursor;if(saved>1)gc_tree_cursor--;{fn}(a,b,c,x,y);gc_tree_cursor=saved;}}\n'
 (O/'browse-global.S').write_text(prefix+'\n'+'\n'.join(entries)+'\n');(O/'browse-values.c').write_text(callbacks)
 with (O/'wizard-usb.S').open('a') as f:
  for name,at in (('mb_native_key',0x400a292c),('mb_native_draw',0x400a24ca)):
   assert image[at-BASE:at-BASE+8]==stock[at-BASE:at-BASE+8]
   f.write(f'.globl {name}\n{name}:\n.byte '+','.join(map(str,stock[at-BASE:at-BASE+8]))+f'\n jmp {at+8:#x}\n')
 assert image[0x400a25e0-BASE:0x400a25e8-BASE]==bytes.fromhex('701841f940071a04')
 with (O/'wizard-usb.S').open('a') as f:f.write('.globl mb_display_hook\nmb_display_hook:\n lea -16(%sp),%sp\n movem.l %d0-%d1/%a0-%a1,(%sp)\n move.l %a2,-(%sp)\n move.l %d3,-(%sp)\n jsr mb_display_machine\n addq.l #8,%sp\n move.l %d0,%d3\n movem.l (%sp),%d0-%d1/%a0-%a1\n lea 16(%sp),%sp\n moveq #24,%d0\n lea 0x40071a04,%a0\n jmp 0x400a25e8\n')
 if a.emac_dsp:
  import re
  original=subprocess.check_output(['git','show','909e6a0:tools/machines/fx_menu/dsp.c'],cwd=R).decode('utf-8')
  body=original[original.index('/* Mixeur EMAC natif.'):original.index('void fx_post(')]
  wet_start=body.index(')for(u32 i=0;i<64;i++){',body.index('/* Gain wet seul'))
  wet_end=body.index('\n#endif',wet_start)
  body=body[:wet_start]+')wet_gain(out);'+body[wet_end:]
  fade_start=body.index(' if(gain!=256||prior_gain!=256)')
  fade_end=body.index('\n#ifdef FX_SIDECHAIN_RETURNS',fade_start)
  body=body[:fade_start]+' if(gain!=256||prior_gain!=256)fade_block(out,prior_gain,gain);'+body[fade_end:]
  if a.reverb_network_opt:
   dispatch_start=body.index(' if(active==0)ch_native')
   default_start=body.index('#ifdef FX_LEAN_FX\n else{',dispatch_start)
   dispatch_end=body.index('#ifdef FX_REVERB101\n /* Gain wet seul',default_start)
   fallback=body[default_start:dispatch_end].replace(' else{',' {')
   dispatch=' switch(active){\n case 0:ch_native(out,in,params);break;\n case 1:case 2:{s16 p[2]={(s16)(fx_speed*256),(s16)(fx_depth*256)};ch_chorus(out,in,p,active,256);break;}\n case 7:fx_ps1(out,in,params);break;\n case 8:fx_room(out,in,params);break;\n case 9:fx_ring(out,in);break;\n case 10:fx_gated(out,in,params);break;\n case 11:fx_hall(out,in,params);break;\n default:{\n'+fallback+'break;}}\n'
   body=body[:dispatch_start]+dispatch+body[dispatch_end:]
  states=('active','ready','gain','prior_gain','correction_on','gain_aux','left','right','aux','effect','correction','dust_target')
  for name in states:
   body=re.sub(r'\b'+name+r'\b','em_state_'+name,body);aliases['em_state_'+name]=m['fx_menu']['symbols'][name]
  for name in ('fx_side','fx_side_on','ch_state','fx_vinyl','fx_vinyl_reset','ch_mode','ch_native','ch_chorus','fx_speed','fx_depth','fx_aux_vi','fx_aux_ch','fx_ps1','fx_room','fx_hall','fx_ring','fx_gated'):
   if name in m['fx_menu']['symbols']:aliases[name]=m['fx_menu']['symbols'][name]
  body=body.replace('void fx_reverb(', 'void em_reverb(')
  declarations='extern u32 em_state_active,em_state_ready,em_state_gain,em_state_prior_gain,em_state_correction_on,em_state_dust_target[2];\nextern s32 em_state_gain_aux[2][6],em_state_left[192],em_state_right[192],em_state_aux[64],em_state_effect[64],em_state_correction[64];\nextern volatile u32 fx_side,fx_side_on;extern u8 ch_state[];extern void fx_vinyl(s32*,const s32*),fx_hall(s32*,const s32*,const s16*);\n'
  (O/'emac-dsp.c').write_text('#include "fx.h"\n#include "emac-math.h"\n'+declarations+body)
 # Installer les relais UI apres les chargeurs2.64 qui possedent les memes slots.
 late=[(0x400a2712,'mb_rotate'),(0x400a292c,'mb_key'),(0x400a25e0,'mb_display_hook'),(m['per_track_fx']['symbols']['rm_step'],'mb_step')]
 for key,target in (('key','mb_gc_key'),('encoder','mb_gc_encoder'),('draw','mb_gc_draw')):late.append((m['groove_strum']['symbols']['gc_'+key],target))
 if network:
  for old,new in (('fx_room','er_room_core'),('fx_hall','er_hall_core'),('fx_ps1_cold','er_ps1_core'),('ps_ap_kernel','er_ps_ap_kernel')):
   aliases[new]=network['symbols'][new];late.append((m['fx_menu']['symbols'][old],new))
 late.append((m['lfo_reload']['symbols']['xp_frame'],'mb_frame'))
 if a.emac_dsp:late.append((m['fx_menu']['symbols']['fx_reverb'],'em_reverb'))
 asm=(O/'wizard-usb.S').read_text(encoding='utf-8');needle=' lea 0x401adbf6,%a1\n'
 extra=''
 for at,fn in late:extra+=f' lea {at:#x},%a1\n move.w #0x4ef9,(%a1)+\n move.l #{fn},(%a1)\n'
 asm=asm.replace(needle,extra+needle)
 if network:
  asm=asm.replace(' lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)',' lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)').replace(' movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp',' movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp')
  copy=f' move.l er_source,%a0\n lea {network["code"]:#x},%a1\n move.l #{len(network_blob)//4},%d0\n.Lnetcopy: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s .Lnetcopy\n'
  asm=asm.replace(' movem.l %d0/%a0-%a1,(%sp)\n',' movem.l %d0/%a0-%a1,(%sp)\n'+copy,1)
  asm+='\n.data\n.balign 4\n.globl er_source\ner_source: .long 0\n'
 (O/'wizard-usb.S').write_text(asm)
 objects=[]
 for src in (O/'lfo.c',O/'punch.c',O/'wizard-usb.S',O/'machine-confirm.c',O/'machine-confirm-menu.c',O/'browse-global.S',O/'browse-values.c')+((O/'emac-dsp.c',) if a.emac_dsp else ()):
  obj=O/(src.stem+'.o');run('gcc','-mcpu=54418','-O3','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-fno-unroll-loops','-DFX_LEAN_FX','-DFX_VOICE_OPT','-DFX_DUST','-DFX_PS1','-DFX_CHEAP','-DFX_EXTRA','-DFX_GATED','-DFX_REVERB101','-DFX_POLISH','-DFX_SIDECHAIN_RETURNS',*(['-DFX_FAST_WRAPPER'] if a.reverb_network_opt else []),'-I',str(R/'tools/machines/fx_menu'),'-I',str(R/'tools/machines/track_fx')] if src.name=='emac-dsp.c' else []),'-c',src,'-o',obj);objects.append(obj)
 (O/'module.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} aa_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 run('ld','-T',O/'module.ld','-e','am_wizard_usb','-o',O/'module.elf',*objects);run('objcopy','-O','binary',O/'module.elf',O/'module.bin');sy={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=BSS and sy['aa_end']<0x46920000
 oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
 # La continuation native ne revient pas : installer avant le saut de fin.
 load=f'.text\n.globl aa_load\naa_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(sy["aa_end"]-BSS+3)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n'
 hooks=[]
 for at,target in ((m['per_track_fx']['symbols']['li_dispatch'],'li_dispatch'),(m['per_track_fx']['symbols']['pp_voice_loop'],'pp_voice_loop'),(0x4000053a,'am_boot_finish')):
  hooks.append(dict(at=at,target=sy[target]));load+=f' lea {at:#x},%a0\n move.l #0x4ef9,%d0\n move.w %d0,(%a0)+\n move.l #{sy[target]:#x},%d0\n move.l %d0,(%a0)\n'
 if network:load+=f' lea {sy["er_source"]:#x},%a0\n move.l #{source+len(blob):#x},(%a0)\n'
 load+=f' movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n';(O/'load.S').write_text(load)
 run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','aa_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
 struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob+network_blob
 from title204_assets import apply as apply_title
 def title_patch(at,old,new,buf):
  assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
 m['title_screen']=apply_title(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,title_patch,'2.65',lite=not full,previous=m['title_screen'])
 dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),ops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
 plains=[]
 for sec in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
 result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/('Supermodel_2.65_EMAC_Reverb_Network_Comparison.syx' if network else 'Supermodel_2.65_EMAC_DSP_Comparison.syx' if a.emac_dsp else 'Supermodel_2.65_Activity_Masks_Experimental.syx')
 if a.check:assert target.read_bytes()==result
 else:target.write_bytes(result)
 m['reverb_network_comparison']=network
 m['emac_dsp_comparison']=dict(enabled=a.emac_dsp,acc3_reserved=False,existing_routing_preserved=True)
 m.update(sha256=sha(result),main_os_sha256=sha(image),activity_masks=dict(loader=loader,previous_loader=oldentry,code=CODE,code_bytes=len(blob),bss=BSS,bss_end=sy['aa_end'],symbols=sy,hooks=hooks,flash_bytes=len(rebuilt),hardware_tested=False,full=full,machine_confirmation=True,late_hooks=[dict(at=at,target=sy[fn]) for at,fn in late]));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT activity masks',len(blob),'code bytes',len(rebuilt),'flash bytes',flush=True)
if __name__=='__main__':main()
