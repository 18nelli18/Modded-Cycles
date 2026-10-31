"""Reverbs exactes : rings physiques masques, EMAC entier et boucles deroulees."""
from pathlib import Path
import hashlib,os,subprocess
CODE=0x468a8000;LIMIT=0x468ae000

def prepare(R,O,m,run):
 S=R/'tools/machines/fx_menu';files=[];assert m['audio_headroom']['hall']['end']<=CODE
 for name,prefix in [('room','room'),('hall','hall'),('ps1','ps')]:
  text=(S/(name+'.c')).read_text(encoding='utf-8')
  text=text.replace('static u32 '+prefix+'_','extern u32 '+prefix+'_').replace('static s32 '+prefix+'_','extern s32 '+prefix+'_')
  if name=='ps1':text=text.replace('static s16 ps_comb','extern s16 ps_comb')
  text=text.replace('void fx_'+name+'_reset(', 'void er_unused_'+name+'_reset(')
  entry='er_'+name+'_core';text=text.replace('void fx_'+name+'(', 'void '+entry+'(')
  signature='void '+entry+'(s32*out,const s32*in,const s16*params){'
  assert signature in text;text=text.replace(signature,signature+'\n struct er_context context;er_enter(&context);')
  end=text.rfind('}');text=text[:end]+' er_leave(&context);\n'+text[end:]
  if name=='ps1':
   text=text.replace('ps_ap[c][at];','ps_ap[c][k*512+((pos-length)&511)];')
   text=text.replace('ps_pos[c][k]=pos+1==length?0:pos+1;','ps_pos[c][k]=(pos+1)&511;')
   text=text.replace('((reflected-low)*(s32)ps_tone)','er_mul(reflected-low,(s32)ps_tone)').replace('(low*(s32)ps_decay)','er_mul(low,(s32)ps_decay)')
  elif name=='room':
   text=text.replace('ps_ap[c][p];','ps_ap[c][(p-n)&127];').replace('room_pos[c]=p+1==n?0:p+1;','room_pos[c]=(p+1)&127;')
   text=text.replace('((old-room_low[c][k])*(s32)room_tone)','er_mul(old-room_low[c][k],(s32)room_tone)').replace('(low*(s32)room_decay)','er_mul(low,(s32)room_decay)')
  else:
   text=text.replace('ps_ap[c][at],x=y;', 'ps_ap[c][k*512+((p-n)&255)],x=y;').replace('hall_pos[c][k]=p+1==n?0:p+1;','hall_pos[c][k]=(p+1)&255;')
   text=text.replace('(old-hall_low[c][k])*(s32)hall_tone','er_mul(old-hall_low[c][k],(s32)hall_tone)').replace('(low*(s32)hall_decay)','er_mul(low,(s32)hall_decay)')
  text=text.replace('s32 old=', 'register s32 old=').replace('s32 low;', 'register s32 low;')
  text='#include "reverb-emac.h"\n'+text
  p=O/('network-'+name+'.c');p.write_text(text,encoding='utf-8');files.append(p)
 hot=(S/'ps1_hot.S').read_text(encoding='utf-8');hot=hot[hot.index('.globl ps_ap_kernel'):].replace('ps_ap_kernel','er_ps_ap_kernel')
 for base,pos,length in (('a2','d4','d6'),('a3','d5','d7')):
  hot=hot.replace(f' mvs.w (%{base},%{pos}.l:2),%d1',f' move.l %{pos},%d1\n sub.l %{length},%d1\n and.l #511,%d1\n mvs.w (%{base},%d1.l:2),%d1')
  old=f' addq.l #1,%{pos}\n cmp.l %{length},%{pos}\n bne 8f\n moveq #0,%{pos}\n8:'
  assert old in hot;hot=hot.replace(old,f' addq.l #1,%{pos}\n and.l #511,%{pos}\n8:')
 hot=hot.replace('1:\n move.l (%a1),%d0','1:\n .rept 2\n move.l (%a1),%d0').replace(' cmp.l %a4,%a0\n bne 1b',' .endr\n cmp.l %a4,%a0\n bne 1b')
 p=O/'network-allpass.S';p.write_text('.text\n'+hot,encoding='utf-8');files.append(p)
 sy=m['fx_menu']['symbols'];aliases={k:v for k,v in sy.items() if k.startswith(('room_','hall_','ps_'))}
 for k,v in m['audio_headroom']['hall']['aliases'].items():aliases[k]=v
 objects=[]
 for src in files:
  obj=src.with_suffix('.o');run('gcc','-mcpu=54418','-O3','-funroll-loops','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-ffunction-sections','-fdata-sections','-DFX_PS1','-DFX_PS1_CACHE_OPT','-DFX_VOICE_OPT','-DFX_POLISH','-I',S,'-I',R/'tools/machines/track_fx','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',src,'-o',obj);objects.append(obj)
 ld=O/'network.ld';ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} er_end = .; .data : {{ *(.data*) }} .bss (NOLOAD) : {{ *(.bss*) *(COMMON) }} }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 elf=O/'network.elf';binary=O/'network.bin';roots=['er_room_core','er_hall_core','er_ps1_core','er_ps_ap_kernel'];run('ld','-T',ld,'--gc-sections','-e',roots[0],*sum((['-u',name] for name in roots[1:]),[]),'-o',elf,*objects);run('objcopy','-O','binary',elf,binary)
 symbols={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3};assert symbols['er_end']<=LIMIT
 return binary.read_bytes(),dict(code=CODE,end=symbols['er_end'],symbols=symbols,allpass_storage=dict(room=[128,128],hall=[256,256,256,256],ps1=[512,512,512,512]),audible_delay_lengths_unchanged=True,new_audio_ram_bytes=0)
