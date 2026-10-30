"""Catalogue prive28machines : IDs25..27, aucun ID existant reutilise."""
from pathlib import Path
import sys,json,re,struct,os
W=Path(os.environ['MD_WORK']);R=Path(__file__).resolve().parents[2];DEV=R;B=W/'probe';S=R/'tools/machines/md'
sys.path[:0]=[str(R/'tools'),str(DEV/'tools')]
import gen_syntakt_engines as gs
import build_machine_identity_test as ident
base=json.loads((R/'tools/machines/md/base-map.json').read_text());tg=base['tg']
gs.LAYOUT.update(STUBS=0x2c0000,DATA=0x13c000,DESCN=0x13c800,ROWSN=0x84000,CCROWSN=0x84400,RECS=0x84800);gs.set_base(0x46700000)
text=gs.detours_asm(21,[1,3,4,4,5]+[4]*13+[0,1,2],[76+5*i for i in range(21)],tg)
names=['map_state','shown','record_at','record_of','knob_vec','desc_machine','builder_row','lfo_gate']
text+='\n'+''.join('.globl '+n+'\n' for n in names)
# Les silhouettes et cartes sont propres aux trois machines, sans changer D3.
old=json.loads((R/'tools/machines/md/base-map.json').read_text());sy=old['tiny_extra']['symbols']
for side in ('left','right'):
 text+=f'\n.globl md_identity_{side}\nmd_identity_{side}:\n'
 for j in range(3):
  text+=f' cmpi.l #{25+j},%d3\n beq.w md_{side}_{j}\n'
 text+=f' cmpi.l #24,%d3\n jmp {sy["tiny_"+side]+6:#x}\n'
 for j in range(3):
  text+=f'md_{side}_{j}:\n'
  text+=(f' lea md_stats_{j},%a1\n suba.l %d4,%a1\n jmp 0x4678812a\n' if side=='left' else f' move.l #md_icon_{j},%d4\n jmp 0x46788144\n')
for j,name in enumerate(('TrxB2','TrxSD','TrxCH')):
 profile=dict(machine=25+j,name=name,icon='M',**{'class':'PERC'},style='MDTRX',str=4,dex=4,mag=3)
 for label,func,width,height in [('stats',ident.stats,48,33),('icon',ident.icon,34,34)]:
  pixels=func(profile);mask=ident.encode([[1]*width for _ in range(height)])
  text+=f'\n.balign 4\nmd_{label}_{j}: .long 0x401117c8,{width},{height},2,md_{label}_{j}_pixels,md_{label}_{j}_mask,0\n'
  for kind,data in [('pixels',pixels),('mask',mask)]:
   p=B/f'md-{label}-{j}-{kind}.bin';p.write_bytes(data);text+=f'md_{label}_{j}_{kind}: .incbin "{p.as_posix()}"\n.balign 2\n'
# Ponts ABI des encodeurs et du dispatch commun (D4=machine, D3=sortie).
text+='''
.globl md_increment,md_dispatch,md_marks
md_increment:
 lea -8(%sp),%sp
 movem.l %a0-%a1,(%sp)
 move.l %d5,-(%sp)
 move.l %d0,-(%sp)
 jsr md_step
 addq.l #8,%sp
 movem.l (%sp),%a0-%a1
 lea 8(%sp),%sp
 moveq #-1,%d1
 jmp 0x400148bc
md_dispatch:
 cmpi.l #6,%d4
 bcs.s 4f
 lea -8(%sp),%sp
 movem.l %d0-%d1,(%sp)
 move.l %d4,%d0
 subq.l #6,%d0
 cmpi.l #22,%d0
 bcc.s 2f
 move.l md_mask,%d1
 lsr.l %d0,%d1
 btst #0,%d1
 beq.s 2f
 movem.l (%sp),%d0-%d1
 lea 8(%sp),%sp
 bra.s 4f
2: movem.l (%sp),%d0-%d1
 lea 8(%sp),%sp
 movea.l %d3,%a0
 moveq #31,%d0
3: clr.l (%a0)+
 subq.l #1,%d0
 bpl.s 3b
 jmp 0x400a7e24
4: cmp.l %d4,%d0
 bcs.s 5f
 jmp 0x46788700
5: jmp 0x400a7e24
md_marks:
 move.l %d3,-(%sp)
 move.l %d2,-(%sp)
 jsr md_draw_marks
 addq.l #8,%sp
 jmp 0x400a26f2
'''
(B/'catalogue.S').write_text(text)
fx=old['fx_menu']['symbols']
c='''typedef unsigned int u32;typedef int s32;
volatile u32 md_mask=0x3fffff;
static const unsigned char order[28]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,21,22,23,24,25,26,27,17};
u32 md_enabled(u32 m){return m<6||(m<28&&((md_mask>>(m-6))&1));}
u32 md_step(u32 m,s32 d){if(!md_enabled(m))m=0;if(!d)return m;u32 at=0;while(at<28&&order[at]!=m)at++;for(s32 i=(s32)at+(d>0?1:-1);i>=0&&i<28;i+=d>0?1:-1)if(md_enabled(order[i]))return order[i];return m;}
'''
c+=f'#define VALID (*(volatile u32*){fx["machine_valid"]:#x})\n#define STAMP (*(volatile u32*){fx["machine_stamp"]:#x})\n#define RESULT (*(volatile u32*){fx["machine_result"]:#x})\n'
c+='''u32 md_fx_step(u32 m,s32 d){if(!d)return md_enabled(m)?m:0;u32 now=*(volatile u32*)0xfc07000c;if(VALID&&m==RESULT&&now-STAMP<5406720u)return m;RESULT=md_step(m,d);VALID=1;STAMP=now;return RESULT;}
void md_draw_marks(u32 canvas,u32 selected){u32 n=0;for(u32 i=0;i<28;i++){u32 id=order[i];if(!md_enabled(id))continue;u32 x=68+5*(n%13),y=9+4*(n/13);((void(*)(u32,u32,u32,u32,u32,u32))(id==selected?0x40070efc:0x40070c4e))(canvas,x-4,y,x,y+3,1);n++;}}
'''
(B/'selection.c').write_text(c)
print('Prepared native catalogue/selector sources for28 machines,181descriptors')
