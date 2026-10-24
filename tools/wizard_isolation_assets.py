"""Banques Wizard/synthese separees pendant le menu MACHINES (v48, note149).
Etat UI seulement, sixpistes; aucune copie ni lecture de banque dans l'audio.
Les CC/changements hors menu et les resets explicites gardent leur chemin natif.
"""
C=r"""
typedef unsigned int u32;typedef unsigned short u16;typedef short i16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern u32 kr_native(u32);extern void kr_bounds(u32,int*);extern u32 kr_menu_native(u32,u32,u32,u32);
static const u32 slot[6]={10,18,11,12,13,14};
typedef struct {u32 obj,valid;u16 synth[4],wizard[4];} Bank;
static Bank banks[6];static u32 active;
static u8 *sound(u32 obj){u32 vt=*(u32*)obj;return vt?(u8*)N(*(u32*)(vt+40))(obj):0;}
static Bank *bank(u32 obj){if(!active)return 0;for(u32 i=0;i<6;i++)if(banks[i].obj==obj)return &banks[i];return 0;}
void kr_fix_snapshot(u32 obj,u32 *v,u32 lane){(void)v;if(lane>=6)return;Bank*b=&banks[lane];b->obj=obj;b->valid=0;u8*p=sound(obj);if(!p||p[38]==17)return;
 u16*dest=p[38]==6?b->wizard:b->synth;for(u32 i=0;i<4;i++)dest[i]=*(u16*)(p+42+i*2);b->valid=p[38]==6?2:1;}
u32 kr_menu(u32 view,u32 delta,u32 all,u32 arg){u32 previous=active;active=view;u32 result=kr_menu_native(view,delta,all,arg);active=previous;return result;}
u32 kr_reset(u32 obj,u32 old){u8*p=sound(obj);if(!p)return kr_native(obj);u32 machine=p[38];if(old==17||machine==17||old>18||machine>18)return kr_native(obj);
 u32 packed=*(u32*)(p+72),tag=packed>>28;u16 before[6];for(u32 i=0;i<6;i++)before[i]=*(u16*)(p+20+slot[i]*2);
 Bank*b=bank(obj);if(b){u16*dest=old==6?b->wizard:b->synth;for(u32 i=0;i<4;i++)dest[i]=before[i+2];b->valid|=old==6?2:1;}
 u32 result=kr_native(obj);p=sound(obj);if(!p||p[38]!=machine)return result;
 if(machine==6&&(tag==7||tag==15))*(u32*)(p+72)=packed;
 for(u32 i=0;i<6;i++){
  u16 value=before[i];
  if(i>=2){if(machine==6){if(b&&(b->valid&2))*(u16*)(p+20+slot[i]*2)=b->wizard[i-2];continue;}
   if(old==6){if(!b||!(b->valid&1))continue;value=b->synth[i-2];}}
  u32 desc=N(0x4005a692)(slot[i],machine);if(!desc)continue;int limits[3];kr_bounds(desc,limits);int bounded=(i16)value;if(bounded<limits[0])bounded=limits[0];if(bounded>limits[1])bounded=limits[1];*(u16*)(p+20+slot[i]*2)=(u16)bounded;
 }
 if(b&&machine==6&&!(b->valid&2)){for(u32 i=0;i<4;i++)b->wizard[i]=*(u16*)(p+42+2*i);b->valid|=2;}
 return result;}
"""
S=r""".text
.globl kr_snapshot
kr_snapshot:
 lea -12(%sp),%sp
 movem.l %d2/%a2-%a3,(%sp)
 move.l %a0,%a2
 move.l 16(%sp),%a3
 move.l %a3,-(%sp)
 jsr 0x400148dc
 addq.l #4,%sp
 move.l %d2,-(%sp)
 move.l %a2,-(%sp)
 move.l %a3,-(%sp)
 jsr kr_fix_snapshot
 lea 12(%sp),%sp
 move.l %a2,%d0
 movem.l (%sp),%d2/%a2-%a3
 lea 12(%sp),%sp
 rts
.globl kr_reset_hook
kr_reset_hook:
 move.l %d5,-(%sp)
 move.l %a2,-(%sp)
 jsr kr_reset
 addq.l #8,%sp
 jmp 0x40014804
.globl kr_menu_native
kr_menu_native:
 lea -60(%sp),%sp
 movem.l %d2-%d7/%a2-%a6,(%sp)
 jmp 0x400a271a
"""
