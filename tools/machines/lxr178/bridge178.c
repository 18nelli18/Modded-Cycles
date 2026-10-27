/* Adaptateur Supermodel original pour ESTUS, port LXR modifie (GPL-3.0-only).
 * Parametres/amp/filtres natifs ; aucun fichier, allocation ou API UI audio. */
typedef int s32;typedef unsigned int u32;typedef short s16;typedef signed char s8;typedef unsigned char u8;
#include "pitch178.h"
extern void lxr_params(s32,const s16*),lxr_fill(s32,u32,s32),lxr178_reset(u32);
s32 sampler_buf[96];u8 dr_trig[8];static u32 steps[6];
const char lxr178_name[]="ESTUS";
#ifdef ESTUS_CONTROLS
char lxr178_labels[5][16] __attribute__((section(".data.lxrlabels")))={"Pitch Amount","Engine","Pitch Decay","FM Drive","Decay"};
char lxr178_short_labels[5][8] __attribute__((section(".data.lxrlabels")))={"PAMT","ENGINE","PTIM","FMDR","DEC"};
#else
const char lxr178_labels[5][16]={"Color","Shape","Sweep","Engine","Decay"};
const char lxr178_short_labels[5][8]={"COLOR","SHAPE","SWEEP","ENGINE","DEC"};
#endif
const char lxr178_modes[8][8]={"KICK","TOM","PERC","SNARE","CLAP","CL HAT","OP HAT","CYMBAL"};
#define V32(o) (*(s32*)(v+(o)))
#define P16(o) (*(const s16*)(p+(o)))
static u32 lane(const char *v){u32 at=(u32)v;if(at<0x42308828u||(at-0x42308828u)%0x31c)return 6;return (at-0x42308828u)/0x31c;}
static s32 clamp(s32 n,s32 lo,s32 hi){return n<lo?lo:n>hi?hi:n;}
void lxr178_update(s32 pmod,char*v,const char*p){
 u32 t=lane(v);if(t>=6)return;
 if((u32)V32(0x2c)!=0x45535455u){lxr178_reset(t);V32(0x2c)=0x45535455u;}
 V32(0x250)=((const s32*)0x4011d84c)[clamp((s8)p[0x24],0,127)];
 if(V32(0x38)){
  V32(0x274)=V32(0x278)=0x012c0f26;V32(0x280)=V32(0x284)=0x001f7c5c;V32(0x290)=V32(0x294)=0x7fffffff;
  V32(0x27c)=(s32)0x82581e4bu;V32(0x288)=(s32)0x803ef8b8u;V32(0x29c)=0x7fffffff;V32(0x2a0)=V32(0x2a4)=0x20000000;V32(0x48)=0;
 }
 /* Le dispatch natif saute le premier update au changement de machine.
  * Son impulsion parametres retardee+38 capture ce premier trig et les retrigs consecutifs. */
 if(V32(0x38))dr_trig[t]=1;
 s32 note=clamp(pmod+(s32)P16(0x14)*256-(64<<16)+((s32)P16(0x22)-0x4000)*8,0,127<<16);
 u32 n=(u32)note>>16,f=(u32)note&65535;steps[t]=note_step[n]+(((note_step[n+1]-note_step[n])>>8)*(f>>8)>>8);
#ifdef ESTUS_CONTROLS
 s16 d[15];
#ifdef ESTUS_ADVANCED
 extern void estus_params(u32,u32);u32 advanced=((u32)(unsigned short)P16(0x34)<<16)|(unsigned short)P16(0x36);
#ifdef ESTUS_PLOCK191
 extern u32 estus_locked_params(u32,u32);advanced=estus_locked_params(t,advanced);
#endif
 estus_params(t,advanced);
#endif
d[11]=P16(0x16);d[12]=P16(0x1a);d[13]=P16(0x1c);d[14]=(s16)clamp(P16(0x18),0,7<<8);lxr_params((s32)t,d);
#else
 lxr_params((s32)t,(const s16*)p);
#endif
}
void lxr178_render(s32*out,char*v){
 u32 t=lane(v);if(t>=6){for(u32 i=0;i<32;i++)out[i]=0;return;}
 u32 a=V32(0x230)<0?0u-(u32)V32(0x230):(u32)V32(0x230),b=V32(0x234)<0?0u-(u32)V32(0x234):(u32)V32(0x234);
 if(!V32(0x34)&&!V32(0x38)&&a<(1<<14)&&b<(1<<14)){lxr178_reset(t);for(u32 i=0;i<32;i++)out[i]=0;return;}
 lxr_fill((s32)t,steps[t],24);
 ((void(*)(char*,s32*,s32*))0x400a9f58)(v,sampler_buf,out);
 ((void(*)(char*))0x400a9252)(v);((void(*)(s32*,char*))0x400a9430)(out,v);
}

/* Appele avant le reset natif : aucun etat ESTUS ne survit au changement de machine. */
void lxr178_reset_voice(char *v){u32 t=lane(v);if(t<6)lxr178_reset(t);}

#ifdef ESTUS_CONTROLS
#define N(a) ((u32(*)())(a))
extern void lxr178_ui_old(void);
extern u32 lxr178_previous_popup(u32,u32,u32,s32,u32,u32);
static u32 label_group=~0u;
static void names(u32 engine){
 u32 g=engine<3?0:engine==3?1:engine==4?2:3;if(g==label_group)return;label_group=g;
 const char *full[4][3]={{"Pitch Amount","Pitch Decay","FM Drive"},{"Noise Mix","Noise Tone","Snap"},{"Spread","Tone","Claps"},{"Tune","Noise",
#ifdef ESTUS_COPY_BUILD
"Bright"
#else
"Brightness"
#endif
}};
 const char *shorts[4][3]={{"PAMT","PTIM","FMDR"},{"NMIX","NTON","SNAP"},{"SPRD","TONE","CLPS"},{"TUNE","NOISE","BRIGHT"}};
 const u32 rows[3]={0,2,3};for(u32 i=0;i<3;i++){for(u32 j=0;j<16;j++)lxr178_labels[rows[i]][j]=0;for(u32 j=0;j<8;j++)lxr178_short_labels[rows[i]][j]=0;u32 j=0;while(full[g][i][j]){lxr178_labels[rows[i]][j]=full[g][i][j];j++;}j=0;while(shorts[g][i][j]){lxr178_short_labels[rows[i]][j]=shorts[g][i][j];j++;}}
}
static u32 selected_engine(void){
 u32 root=*(volatile u32*)0x40fe4228;if(!root)return 8;u32 t=N(0x40012412)(root+48);if(t>=6)return 8;
 u32 obj=N(0x40009c1a)(root+116,t),vt=*(const u32*)obj;if(!vt)return 8;u8 *raw=(u8*)N(*(const u32*)(vt+40))(obj);if(!raw)return 8;
#ifdef ESTUS_PLOCK191
 extern u32 estus_edit_info(u32,u32,u32);u32 info=estus_edit_info(t,raw[38],raw[44]);if(info>>8!=24)return 8;return (u32)clamp(info&255,0,7);
#else
 if(raw[38]!=24)return 8;return (u32)clamp(raw[
#ifdef ESTUS_ENGINE_READ
44
#else
24
#endif
],0,7);
#endif
}
void lxr178_ui_frame(void){lxr178_ui_old();if(!*(volatile u32*)0x40fe4178
#ifndef ESTUS_LIVE187
||*(volatile u32*)0x40a7883c
#endif
)return;u32 e=selected_engine();if(e<8)names(e);}
u32 lxr178_popup(u32 view,u32 canvas,u32 desc,s32 value,u32 flags,u32 last){
 u32 e=desc==162?(u32)clamp(value>>8,0,7):selected_engine();if(e<8)names(e);
 u32 result=lxr178_previous_popup(view,canvas,desc,value,flags,last);if(desc!=162)return result;
 N(0x40070efc)(canvas,64,29,127,63,0);N(0x40071a04)(canvas,0x40ea14cc,96,43,2,"%s",lxr178_modes[e]);return result;
}
#endif

#ifdef ESTUS_ADVANCED
void *memcpy(void*d,const void*s,unsigned long n){u8 *a=d;const u8*b=s;while(n--)*a++=*b++;return d;}
extern volatile u32 estus_menu,estus_fx_open,estus_wf_api[];
extern void estus_notice(const char*);
extern u32 estus_old_encoder(u32,const u32*);
static u32 adv_stamp,adv_knob,adv_delta,adv_valid;
u32 estus_encoder(u32 view,const u32*e){
 if(!e||e[0]!=0x400fbebc||e[3]<4||e[3]>7||estus_menu||estus_fx_open||!N(0x4007faf4)(13)||N(0x4007faf4)(1)||N(0x4007faf4)(2)||N(0x4007faf4)(8))return estus_old_encoder(view,e);
 u32 root=*(volatile u32*)0x40fe4228;if(!root||!*(volatile u32*)0x40fe4178
#ifndef ESTUS_LIVE187
||*(volatile u32*)0x40a7883c
#endif
)return estus_old_encoder(view,e);
 u32 t=N(0x40012412)(root+48);if(t>=6)return estus_old_encoder(view,e);
 u32 obj=N(0x40009c1a)(root+116,t),vt=*(u32*)obj;if(!vt)return estus_old_encoder(view,e);
 u8 *raw=(u8*)N(*(u32*)(vt+40))(obj);if(!raw)return estus_old_encoder(view,e);
#ifdef ESTUS_PLOCK191
 extern void estus_lock_warm(void);extern u32 estus_edit_info(u32,u32,u32);estus_lock_warm();u32 edit_info=estus_edit_info(t,raw[38],raw[44]);if(edit_info>>8!=24)return estus_old_encoder(view,e);
#else
 if(raw[38]!=24)return estus_old_encoder(view,e);
#endif
 if(estus_wf_api[5])*(volatile u32*)estus_wf_api[5]=1;
 if(e[2]&&adv_valid&&adv_stamp==e[2]&&adv_knob==e[3]&&adv_delta==e[4])return 1;
 adv_valid=1;adv_stamp=e[2];adv_knob=e[3];adv_delta=e[4];
 u32 packed=((u32)raw[72]<<24)|((u32)raw[73]<<16)|((u32)raw[74]<<8)|raw[75];
 if((packed>>28)!=10)packed=0xa0000040u;
 u32 field=e[3]-4,shift=21-7*field,old=(packed>>shift)&127;
 u32 engine=
#ifdef ESTUS_PLOCK191
 edit_info&255;
#else
 raw[
#ifdef ESTUS_ENGINE_READ
44
#else
24
#endif
];
#endif
 if((field==0&&engine==4)||(field==1&&(engine==3||engine==4))){estus_notice("NOT USED BY ENGINE");return 1;}
 s32 delta=(s32)N(0x4006f73a)(e,1,1),max=field==0?4:field==1?16:127;
 s32 value=clamp((s32)old+delta,0,max);
#ifdef ESTUS_PLOCK191
 extern u32 estus_lock_edit(u32,u32,s32,u32*);u32 locked=0,lock_value=(u32)value;locked=estus_lock_edit(t,field,delta,&lock_value);if(locked)value=(s32)lock_value;
#endif
 packed=(packed&~(127u<<shift))|((u32)value<<shift);
 #ifdef ESTUS_PLOCK191
 if(!locked){
#endif
 u32 records[4]={26,packed&0xffff0000u,27,packed<<16};u32 pair[2]={(u32)records,(u32)(records+4)};N(0x4001416c)(obj,pair);
#ifdef ESTUS_PLOCK191
 }
#endif
 char text[48];const char *waves[5]={"DEFAULT","SINE","TRIANGLE","SAW","SQUARE"};
 const char *ratios[17]={"DEFAULT","1/4","1/3","1/2","2/3","1","3/2","2","5/2","3","4","5","6","7","8","12","16"};
 if(field==0)N(0x40000e6e)(text,"WAVE %s",waves[value]);
 else if(field==1)N(0x40000e6e)(text,"FM RATIO %s",ratios[value]);
 else if(field==2){if(!value)N(0x40000e6e)(text,"DRIVE DEFAULT");else N(0x40000e6e)(text,"DRIVE %u",value-1);}
 else N(0x40000e6e)(text,"TRANSIENT %u",value);
 estus_notice(text);return 1;
}
#endif
