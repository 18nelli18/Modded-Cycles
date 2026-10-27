/* SPDX-License-Identifier: MIT
 * Mode Performance : quinze macros, quatre destinations chacune.
 * Sources autonomes de la contribution experimentale (notes/58).
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef signed int s32;
void *memset(void *dst,int byte,u32 count){u8 *p=(u8*)dst;while(count--)*p++=(u8)byte;return dst;}
#define DATA __attribute__((section(".data"),aligned(4)))
#define CALL(a,t) ((t)(u32)(a))
typedef struct {u8 track,dest,on,pad; s16 depth;u16 reserved;} Route;
_Static_assert(sizeof(u32)==4&&sizeof(u16)==2&&sizeof(Route)==8,"stock parameter ABI");
extern u32 per_level_stock(void*,void*),per_param_stock(void*,void*),per_key_bridge_stock(void*,void*);
extern u32 per_key_stock(void*,void*),per_param_key_stock(void*,void*);
extern void per_publish_stock(u32,const u16*),per_incremental_stock(u32,void*,void*),per_draw_stock(void*,void*);
volatile u32 per_mode DATA=0,per_selected DATA=0,per_route DATA=0,per_initialized DATA=0,per_level_owned DATA=0;
volatile u32 per_main_view DATA=0,per_gesture_owned DATA=0,per_click_suppress DATA=0,per_back_owned DATA=0,per_gate_owned DATA=0;
volatile u32 per_amounts[15] DATA={0};
#include "performance_registry.generated.h"
#include "performance_registry_runtime.h"
volatile s32 per_fx_sums[PER_FX_COUNT] DATA={0};
volatile u32 per_fx_mask DATA=0;
volatile Route per_routes[15][4] DATA={0};
volatile Route per_clip_routes[4] DATA={0};
volatile u32 per_clip_amount DATA=0,per_clip_owner DATA=0,per_clip_valid DATA=0;
volatile u32 per_clip_owned DATA=0,per_clip_suppress DATA=0,per_clip_notice DATA=0,per_clip_ticks DATA=0;

static u32 key(u32 k){return CALL(0x4007faf4,u32(*)(u32))(k);}
static void *ui(void){return CALL(0x400cf9a8,void*(*)(void))();}
static u32 blocked(void){
 void *p=ui();
 return CALL(0x4006b978,u32(*)(void*))(p)&255 ||
        CALL(0x4006bb18,u32(*)(void*))(p)&255 ||
        CALL(0x4006b704,u32(*)(void*))(p)&255 || CALL(0x4006ba76,u32(*)(void*))(p)&255;
}
static s32 clamp(s32 v,s32 lo,s32 hi){return v<lo?lo:v>hi?hi:v;}
static s32 delta(void *event){return (s16)CALL(0x4006f73a,s32(*)(void*,u32,u32))(event,1,8);}
static u32 mask(u32 m){if(m>=15)return 0;u32 b=0;for(u32 j=0;j<4;j++)if(per_routes[m][j].depth!=0&&per_routes[m][j].track<7)b|=1u<<per_routes[m][j].track;return b;}

volatile u32 per_level_mask DATA=0;
volatile s32 per_level_sums[6] DATA={0};
volatile s32 per_sound_sums[6][PER_SOUND_COUNT] DATA={0};
volatile u32 per_sound_mask[6] DATA={0};

volatile u16 per_level_audio[240] DATA={0};
static void level_overlay(u32 t,u32 base,s32 sum,u32 touched){
 u32 bit=1u<<t;per_level_sums[t]=touched?sum:0;
 if(touched)per_level_mask|=bit;else per_level_mask&=~bit;
}
void per_storage_observe(void);
/* Trame audio native en SRAM : seuls les mots routes sont echanges.
 * Masquer les interruptions jusqu'a leur restauration, avant les LFO et les
 * observateurs. Les autres sources gardent le chemin de copie autonome. */
static u32 storage_irq_lock(void);
static void storage_irq_restore(u32);
static u32 per_audio_onchip(volatile u16 *frame){
 u32 irq=storage_irq_lock(),levels=per_level_mask,fx=per_fx_mask,sound[6];
 for(u32 t=0;t<6;t++){
  sound[t]=per_sound_mask[t];
  if(levels&(1u<<t)){
   u16 base=frame[t];per_level_audio[t]=base;
   frame[t]=clamp((s32)base+per_level_sums[t],0,0x7f00);
  }
  if(!sound[t])continue;
  for(u32 d=0;d<PER_SOUND_COUNT;d++)if(sound[t]&(1u<<d)){
   const PerParameter *p=&per_track_params[d];u32 slot=7+t*33+p->slot;
   u16 base=frame[slot];per_level_audio[slot]=base;
   frame[slot]=per_param_value(p,(s32)base+per_sound_sums[t][d]);
  }
 }
 for(u32 d=0;d<PER_FX_COUNT;d++)if(fx&(1u<<d)){
  const PerParameter *p=&per_fx_params[d];u32 slot=205+p->slot;
  u16 base=frame[slot];per_level_audio[slot]=base;
  frame[slot]=per_param_value(p,(s32)base+per_fx_sums[d]);
 }
 u32 result=CALL(0x40058474,u32(*)(const u16*))((const u16*)frame);
 for(u32 t=0;t<6;t++){
  if(levels&(1u<<t))frame[t]=per_level_audio[t];
  if(!sound[t])continue;
  for(u32 d=0;d<PER_SOUND_COUNT;d++)if(sound[t]&(1u<<d)){
   u32 slot=7+t*33+per_track_params[d].slot;frame[slot]=per_level_audio[slot];
  }
 }
 for(u32 d=0;d<PER_FX_COUNT;d++)if(fx&(1u<<d)){
  u32 slot=205+per_fx_params[d].slot;frame[slot]=per_level_audio[slot];
 }
 storage_irq_restore(irq);return result;
}
u32 per_audio_levels(const u16 *source){
 per_storage_observe();
 u32 active=per_level_mask|(per_fx_mask?64:0);for(u32 t=0;t<6;t++)if(per_sound_mask[t])active|=1u<<t;
 if(!source||!per_initialized||!active)return CALL(0x40058474,u32(*)(const u16*))(source);
 if((u32)source==0x800015a0u)return per_audio_onchip((volatile u16*)source);
 for(u32 i=0;i<238;i++)per_level_audio[i]=source[i];
 for(u32 t=0;t<6;t++){
  if(per_level_mask&(1u<<t))per_level_audio[t]=clamp((s32)source[t]+per_level_sums[t],0,0x7f00);
  u32 touched=per_sound_mask[t];if(!touched)continue;
  for(u32 d=0;d<PER_SOUND_COUNT;d++)if(touched&(1u<<d)){
   const PerParameter *p=&per_track_params[d];u32 slot=7+t*33+p->slot;
   per_level_audio[slot]=per_param_value(p,(s32)source[slot]+per_sound_sums[t][d]);
  }
 }
 for(u32 d=0;d<PER_FX_COUNT;d++)if(per_fx_mask&(1u<<d)){
  const PerParameter *p=&per_fx_params[d];u32 slot=205+p->slot;per_level_audio[slot]=per_param_value(p,(s32)source[slot]+per_fx_sums[d]);
 }
 return CALL(0x40058474,u32(*)(const u16*))((const u16*)per_level_audio);
}
static void level_from_routes(u32 t,u32 base){
 if(!per_initialized||t>=6)return;
 s32 sum=0;u32 touched=0;
 for(u32 m=0;m<15;m++){
  u32 amount=per_amounts[m];if(!amount)continue;if(amount>127)amount=127;
  for(u32 j=0;j<4;j++){volatile Route *r=&per_routes[m][j];s32 depth=r->depth;
   if(r->pad||r->track!=t||r->dest!=per_track_params[PER_LEVEL_INDEX].id||!depth||depth < -127||depth>127)continue;
   volatile s32 divisor=127;sum+=(depth*256*(s32)amount)/divisor;touched=1;
  }
 }
 level_overlay(t,base,sum,touched);
}
static void per_storage_edit(void);
extern void per_track_level_stock(u32,u32,void*),per_kit_stock(void*);
void per_track_level(u32 t,u32 value,void *cache){per_track_level_stock(t,value,cache);level_from_routes(t,value);}
extern volatile u32 per_active_kit,per_storage_reload;
void per_storage_load(const void *kit);
void per_kit(void *kit){if(kit&&per_storage_reload&&(u32)kit==per_active_kit)per_storage_load(kit);u32 previous=per_level_mask;per_kit_stock(kit);per_level_mask|=previous;if(kit&&per_initialized)for(u32 t=0;t<6;t++)level_from_routes(t,((u16*)((u8*)kit+16))[t]);}

void per_apply(u32 track,const u16 *source){
 if(!per_initialized||track>=7||!source)return;
 if(track==6){
  s32 sums[PER_FX_COUNT]={0};u32 touched=0;
  for(u32 m=0;m<15;m++){
   u32 amount=per_amounts[m];if(!amount)continue;if(amount>127)amount=127;
   for(u32 j=0;j<4;j++){volatile Route *r=&per_routes[m][j];s32 depth=r->depth;
    if(r->pad||r->track!=6||!depth||depth < -127||depth>127)continue;
    s32 d=per_param_index(6,r->dest);if(d<0)continue;
    volatile s32 divisor=127;sums[d]+=(depth*256*(s32)amount)/divisor;touched|=1u<<d;
   }
  }
  per_fx_mask=touched;
  volatile u32 *out=(volatile u32*)(0x80001204u+6*132u);
  for(u32 d=0;d<PER_FX_COUNT;d++){const PerParameter *p=&per_fx_params[d];per_fx_sums[d]=sums[d];if(touched&(1u<<d))out[p->slot]=(u32)per_param_value(p,(s32)source[p->slot]+sums[d])<<16;}
  return;
 }
 s32 sums[PER_TRACK_COUNT]={0};u32 touched=0;
 for(u32 m=0;m<15;m++){
  u32 amount=per_amounts[m];if(!amount)continue;if(amount>127)amount=127;
  for(u32 j=0;j<4;j++){
   volatile Route *r=&per_routes[m][j];
   u32 t=r->track;s32 depth=r->depth;
   if(r->pad||!depth||t!=track||depth < -127||depth>127)continue;
   s32 d=per_param_index(track,r->dest);if(d<0)continue;

   volatile s32 divisor=127;
   sums[d]+=(depth*256*(s32)amount)/divisor;touched|=1u<<d;
  }
 }
 for(u32 d=0;d<PER_SOUND_COUNT;d++)per_sound_sums[track][d]=sums[d];
 per_sound_mask[track]=touched&((1u<<PER_SOUND_COUNT)-1);
 volatile u32 *out=(volatile u32*)(0x80001204u+track*132u);
 for(u32 d=0;d<PER_SOUND_COUNT;d++)if(touched&(1u<<d)){
  const PerParameter *p=&per_track_params[d];
  out[p->slot]=(u32)per_param_value(p,(s32)source[p->slot]+sums[d])<<16;
 }
 level_overlay(track,((const u16*)0x800015a0u)[track],sums[PER_LEVEL_INDEX],touched&(1u<<PER_LEVEL_INDEX));
}
void per_publish(u32 track,const u16 *source){per_publish_stock(track,source);per_apply(track,source);}
void per_incremental(u32 track,void *cache,void *source){
 per_incremental_stock(track,cache,source);
 if(track<7)per_apply(track,(const u16*)((u8*)cache+14+track*66));
}
void per_refresh(u32 tracks){
 for(u32 t=0;t<7;t++)if(tracks&(1u<<t))per_publish(t,(const u16*)(0x800015aeu+t*66u));
}
#include "performance_storage_runtime.h"
#include "performance_project_settings.h"

static u32 per_ui_state_ok(void){
 u32 bad=per_mode>2||per_selected>=15||per_route>=4;
 for(u32 m=0;m<15;m++)if(per_amounts[m]>127)bad=1;
 if(!bad&&per_mode==2)for(u32 j=0;j<4;j++){volatile Route *r=&per_routes[per_selected][j];if(r->track>6||r->depth < -127||r->depth>127)bad=1;}
 if(!bad)return 1;
 per_mode=per_selected=per_route=0;storage_clear_offsets();per_storage_fault++;return 0;
}
static void invalidate(void *view){
 CALL(0x40076082,void(*)(void*))(view);
 if(per_main_view&&(u32)view!=per_main_view)CALL(0x40076082,void(*)(void*))((void*)per_main_view);
}

extern void per_root_key_stock(void*,void*);
static void per_clip_action(u32 id){
 per_storage_observe();
 u32 irq=storage_irq_lock(),project=*(volatile u32*)0x406fa02cu;
 if(per_clip_valid&&per_clip_owner!=project)per_clip_valid=0;
 u32 m=per_selected,notice=0;s32 slot=per_storage_slot((void*)per_active_kit,1);
 if(m>=15||!per_active_pattern||slot<0)notice=5;
 else if(id==9){
  for(u32 j=0;j<4;j++)per_clip_routes[j]=per_routes[m][j];
  per_clip_amount=per_amounts[m];per_clip_owner=project;per_clip_valid=1;notice=1;
 }else if(id==11&&!per_clip_valid)notice=4;
 else{
  if(id==10){for(u32 j=0;j<4;j++){volatile Route *r=&per_routes[m][j];r->track=r->dest=r->on=r->pad=0;r->depth=0;r->reserved=0;}per_amounts[m]=0;notice=2;}
  else{for(u32 j=0;j<4;j++)per_routes[m][j]=per_clip_routes[j];per_amounts[m]=per_clip_amount;notice=3;}
  for(u32 t=0;t<7;t++)per_apply(t,(const u16*)(0x800015aeu+t*66u));
  per_record_routes((u8*)storage_pending(slot));storage_publish(slot);
 }
 per_clip_notice=notice;per_clip_ticks=120;storage_irq_restore(irq);
 if(notice==2||notice==3)per_storage_edit_notice(slot);
 if(per_main_view)invalidate((void*)per_main_view);
}
void per_root_key(void *root,void *event){
 if(event&&*(u32*)event==0x400fc20cu){
  u32 id=((u32*)event)[3],flags=((u32*)event)[4];
  if(id>=9&&id<=11){u32 bit=1u<<(id-9);
   if(per_clip_owned&bit){if(!(flags&1))per_clip_owned&=~bit;if(flags&16)per_clip_suppress&=~bit;return;}
   if((flags&1)&&!(flags&8))per_clip_suppress&=~bit;
   if((flags&16)&&(per_clip_suppress&bit)){per_clip_suppress&=~bit;return;}
   if(per_mode&&per_main_view&&!*((u8*)per_main_view+0x17)&&(key(1)||(flags&2))){

    if((flags&1)&&!(flags&8)){
     per_clip_owned|=bit;per_clip_suppress|=bit;
     if(per_ui_state_ok()&&!blocked()&&!key(2)&&!key(3)&&!key(4))per_clip_action(id);
    }
    return;
   }
  }
 }
 per_root_key_stock(root,event);
}
static u32 active_track(void){
 void *p=CALL(0x400cf866,void*(*)(void))();
 p=CALL(0x4000eb90,void*(*)(void*))(p);
 return CALL(0x40012412,u32(*)(void*))(p);
}

s32 per_descriptor_macro(u32 p){
 if(p==42||p==43)return 0;
 if(p==24)return 1;
 if(p>=46&&p<=75){static const u8 mapped[30]={2,3,5,6,1,2,3,5,6,1,2,3,5,6,1,2,3,5,6,1,2,3,5,6,1,2,3,5,6,1};return mapped[p-46];}
 if(p==26)return 7;
 if(p==27)return 8;
 if(p==29)return 10;
 if(p==25)return 11;
 if(p==23)return 12;
 if(p==22)return 13;
 if(p==39)return 9;
 if(p==37)return 14;
 return -1;
}
u32 per_parameter(void *view,void *event){
 if(!per_ui_state_ok())return 1;
 u32 id=((u32*)event)[3];
 if(!per_mode||id<2||id>15)return per_param_stock(view,event);
 if(blocked()||key(2)||key(3)||key(4))return 1;

 u32 descriptor=CALL(0x4001e814,u32(*)(void*,u32,u32,s32))(view,id,0,-1);
 s32 m=per_descriptor_macro(descriptor);
 if(m<0)return 1;
 s32 change=delta(event);if(!change)return 1;
 if(per_mode==2){
  volatile Route *r=&per_routes[per_selected][per_route];
  u32 old=mask(per_selected),enabled=r->on;r->on=0;
  if(m==0){r->on=enabled;per_route=clamp((s32)per_route+change,0,3);}
  else if(m==1){r->track=clamp((s32)r->track+change,0,6);if(per_param_index(r->track,r->dest)<0)r->dest=per_param_next_for(per_profile_for_track(r->track),r->track,0,0);}
  else if(m==2)r->dest=per_param_next_for(per_profile_for_track(r->track),r->track,r->dest,change);
  else if(m==3)r->depth=clamp((s32)r->depth+change,-127,127);

  r->on=enabled;if(m==1||m==2){r->reserved=0;r->pad=0;}if(m==1||m==2||m==3)per_storage_edit();per_refresh(old|mask(per_selected));
 }else{
  per_selected=(u32)m;per_amounts[m]=clamp((s32)per_amounts[m]+change,0,127);per_storage_edit();per_refresh(mask((u32)m));
 }
 invalidate(view);return 1;
}

static u32 open_mode(void *view){
 if(blocked())return 0;
 {
  if(!per_initialized)per_initialized=1;
  per_mode=1;
 }
 per_gesture_owned=1;invalidate(view);return 1;
}
u32 per_level(void *view,void *event){
 if(!per_ui_state_ok())return 1;
 if(((u32*)event)[3]!=1)return per_level_stock(view,event);
 if(!per_mode)return per_level_stock(view,event);
 if(blocked()||key(2)||key(3)||key(4))return 1;
 per_selected=clamp((s32)per_selected+(s16)CALL(0x4006f73a,s32(*)(void*,u32,u32))(event,1,1),0,14);
 invalidate(view);return 1;
}
static u32 handle_key(void *view,void *event){
 per_ui_state_ok();
 u32 id=((u32*)event)[3],flags=((u32*)event)[4];
 if(per_mode&&per_main_view&&!*((u8*)per_main_view+0x17)&&(id==3||id==13)&&(key(1)||(flags&2)))return per_storage_key(id,flags);
 if(id==1&&!(flags&1)){per_gesture_owned=0;return 0;}

 if(id==7){
  if((flags&1)&&!(flags&8)&&!per_gate_owned&&(key(1)||(flags&2))&&!key(2)&&!key(3)&&!key(4)){
   open_mode(view);per_gate_owned=1;return 1;
  }
  if(per_gate_owned){if(!(flags&1))per_gate_owned=0;return 1;}
 }
 if(id==32){
  u32 down=(flags&1)&&!(flags&8);

  if(down&&!per_level_owned){
   per_click_suppress=0;
   u32 func=key(1)||(flags&2);
   if(per_mode&&!func&&!key(2)&&!key(3)&&!key(4)){
    if(!blocked()){per_mode=per_mode==2?1:2;invalidate(view);}
    per_level_owned=1;per_click_suppress=1;return 1;
   }
  }
  if(per_level_owned){if(!(flags&1))per_level_owned=0;return 1;}

  if((flags&16)&&per_click_suppress){per_click_suppress=0;return 1;}
 }
 if((per_mode||per_back_owned)&&id==12){
  if((flags&1)&&!(flags&8)&&!per_back_owned){per_back_owned=1;if(per_mode==2)per_mode=1;else per_mode=0;invalidate(view);}
  if(!(flags&1))per_back_owned=0;
  return 1;
 }
 return 0;
}

u32 per_key_bridge(void *capture,void *recipient){
 void *event=**(void***)capture;

 u32 owned_view=(u32)recipient==per_main_view;
 if(!owned_view&&recipient){u32 *vtable=*(u32**)recipient;owned_view=vtable&&vtable[2]==0x4001f97e;}

 u32 perf_back=per_main_view&&((u32*)event)[3]==12&&(per_mode||per_back_owned)&&!*((u8*)per_main_view+0x17);

 u32 perf_level=per_main_view&&((u32*)event)[3]==32&&(per_mode||per_level_owned||per_click_suppress)&&!*((u8*)per_main_view+0x17);
 u32 perf_storage=per_main_view&&per_mode&&(((u32*)event)[3]==3||((u32*)event)[3]==13)&&(((u32*)event)[4]&2)&&!*((u8*)per_main_view+0x17);
 if(per_main_view&&(owned_view||perf_back||perf_level||perf_storage)&&handle_key((void*)per_main_view,event))return 1;
 return per_key_bridge_stock(capture,recipient);
}
u32 per_main_key(void *view,void *event){per_main_view=(u32)view;return handle_key(view,event)?1:per_key_stock(view,event);}
u32 per_parameter_key(void *view,void *event){
 if(handle_key(view,event)){
  if(((u32*)event)[3]==32&&(((u32*)event)[4]&16))CALL(0x4001ef0e,void(*)(void*))(view);
  return 1;
 }
 return per_param_key_stock(view,event);
}
void per_tick(void *context){
 per_storage_observe();
 if(per_clip_ticks&&!--per_clip_ticks){per_clip_notice=0;if(per_mode&&per_main_view)invalidate((void*)per_main_view);}
 if(!key(1))per_gesture_owned=0;
 CALL(0x40090f48,void(*)(void*))(context);
}

const u8 per_font[40][7]={
 {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},{30,1,1,14,1,1,30},
 {2,6,10,18,31,2,2},{31,16,16,30,1,1,30},{14,16,16,30,17,17,14},{31,1,2,4,8,8,8},
 {14,17,17,14,17,17,14},{14,17,17,15,1,1,14},
 {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{15,16,16,16,16,16,15},{30,17,17,17,17,17,30},
 {31,16,16,30,16,16,31},{31,16,16,30,16,16,16},{15,16,16,19,17,17,15},{17,17,17,31,17,17,17},
 {14,4,4,4,4,4,14},{7,2,2,2,2,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
 {17,27,21,21,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},{30,17,17,30,16,16,16},
 {14,17,17,17,21,18,13},{30,17,17,30,20,18,17},{15,16,16,14,1,1,30},{31,4,4,4,4,4,4},
 {17,17,17,17,17,17,14},{17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},
 {17,17,10,4,4,4,4},{31,1,2,4,8,16,31},
 {0,4,4,0,4,4,0},{0,0,0,31,0,0,0},{0,4,4,31,4,4,0},{0,0,0,0,0,0,0}
};
static void pixel(void *bitmap,u32 x,u32 y){
 u32 stride=((u32*)bitmap)[3];u32 *pixels=(u32*)((u32*)bitmap)[4];
 if(x<128&&y<64&&stride==2)pixels[x*stride+(y>>5)]|=1u<<(31-(y&31));
}
static void glyph(void *b,u32 x,u32 y,char c){
 u32 n=c>='0'&&c<='9'?c-'0':c>='A'&&c<='Z'?c-'A'+10:c==':'?36:c=='-'?37:c=='+'?38:39;
 for(u32 row=0;row<7;row++)for(u32 col=0;col<5;col++)if(per_font[n][row]&(16u>>col))pixel(b,x+col,y+6-row);
}
static void text(void *b,u32 x,u32 y,const char *s){for(;*s&&x<128;s++,x+=6)glyph(b,x,y,*s);}

static __attribute__((noinline)) u32 divide10(u32 n){volatile u32 divisor=10;return n/divisor;}
static void number(void *b,u32 x,u32 y,u32 n,u32 width){
 for(u32 i=0;i<width;i++){u32 q=divide10(n);glyph(b,x+6*(width-1-i),y,'0'+n-q*10);n=q;}
}
static void line(void *b,u32 x,u32 y,u32 width){for(u32 i=0;i<width;i++)pixel(b,x+i,y);}
static void invert(void *bitmap,u32 x,u32 y,u32 width,u32 height){
 u32 stride=((u32*)bitmap)[3];u32 *pixels=(u32*)((u32*)bitmap)[4];
 for(u32 xx=x;xx<x+width&&xx<128;xx++)for(u32 yy=y;yy<y+height&&yy<64;yy++)pixels[xx*stride+(yy>>5)]^=1u<<(31-(yy&31));
}

const u8 per_small_font[40][5]={
 {7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7},
 {2,5,7,5,5},{6,5,6,5,6},{3,4,4,4,3},{6,5,5,5,6},{7,4,6,4,7},{7,4,6,4,4},{3,4,5,5,3},{5,5,7,5,5},{7,2,2,2,7},{1,1,1,5,2},{5,5,6,5,5},{4,4,4,4,7},{5,7,7,5,5},{5,7,7,7,5},{2,5,5,5,2},{6,5,6,4,4},{2,5,5,3,1},{6,5,6,5,5},{3,4,2,1,6},{7,2,2,2,2},{5,5,5,5,7},{5,5,5,5,2},{5,5,7,7,5},{5,5,2,5,5},{5,5,2,2,2},{7,1,2,4,7},{0,2,0,2,0},{0,0,7,0,0},{0,2,7,2,0},{0,0,0,0,0}
};
const u8 per_amount_font[10][10]={
 {0,31,17,17,17,21,17,17,17,31},{4,4,12,4,4,4,4,4,4,4},{30,30,1,1,1,14,16,16,16,31},{30,30,1,1,1,14,1,1,1,30},{18,18,18,18,18,31,2,2,2,2},{31,31,16,16,16,30,1,1,1,30},{15,15,16,16,16,30,17,17,17,14},{31,31,1,1,2,4,4,8,8,8},{14,14,17,17,17,14,17,17,17,14},{14,14,17,17,17,15,1,1,1,30}
};
static u32 glyph_index(char c){return c>='0'&&c<='9'?c-'0':c>='A'&&c<='Z'?c-'A'+10:c==':'?36:c=='-'?37:c=='+'?38:39;}
static void small_text(void *b,u32 x,u32 y,const char *s){
 for(;*s&&x<128;s++,x+=4)for(u32 r=0;r<5;r++)for(u32 c=0;c<3;c++)if(per_small_font[glyph_index(*s)][r]&(4u>>c))pixel(b,x+c,y+4-r);
}
static void small_number(void *b,u32 x,u32 y,u32 n){if(n>=10){char digit[2]={'1',0};small_text(b,x,y,digit);x+=4;n-=10;}char digit[2]={'0'+n,0};small_text(b,x,y,digit);}
static void amount_number(void *b,u32 x,u32 y,u32 n){
 u32 width=n>=100?3:n>=10?2:1;
 for(u32 i=0;i<width;i++){u32 q=divide10(n),d=n-q*10;for(u32 r=0;r<10;r++)for(u32 c=0;c<5;c++)if(per_amount_font[d][r]&(16u>>c))pixel(b,x+23-6*(i+1)+c,y+9-r);n=q;}
}
static void header_glyph(void *b,u32 x,u32 y,char c){
 for(u32 r=0;r<9;r++)for(u32 col=0;col<5;col++){
  u8 bits=c>='0'&&c<='9'?per_amount_font[c-'0'][r+1]:per_font[glyph_index(c)][r*7/9];
  if(bits&(16u>>col))pixel(b,x+col,y+8-r);
 }
}
static void header_text(void *b,u32 x,const char *s){for(;*s;s++,x+=6)header_glyph(b,x,55,*s);}
static void header_number(void *b,u32 n){u32 tens=divide10(n),x=42;if(tens){header_glyph(b,x,55,'0'+tens);x+=6;}header_glyph(b,x,55,'0'+n-tens*10);}
static const char *per_clip_message(void){return per_clip_notice==1?"COPIED":per_clip_notice==2?"CLEARED":per_clip_notice==3?"PASTED":per_clip_notice==4?"EMPTY":"NO PATTERN";}
void per_draw(void *view,void *bitmap){
 per_main_view=(u32)view;
 per_draw_stock(view,bitmap);if(!per_ui_state_ok()||blocked())return;
 if(!per_mode)return;
 u32 stride=((u32*)bitmap)[3];u32 *pixels=(u32*)((u32*)bitmap)[4];if(stride!=2||!pixels)return;
 for(u32 i=0;i<256;i++)pixels[i]=0;
 if(per_mode==1){
  header_text(bitmap,0,"PERF");header_text(bitmap,36,"M");header_number(bitmap,per_selected+1);line(bitmap,0,54,128);
  u32 x=0,y=38;
  for(u32 m=0;m<15;m++){
   small_number(bitmap,x+1,y+10,m+1);amount_number(bitmap,x,y,per_amounts[m]);
   if(m==per_selected)invert(bitmap,x,y,x==104?24:25,15);
   x+=26;if(x==130){x=0;y-=16;}
  }
  small_text(bitmap,0,0,per_clip_notice?per_clip_message():"LEVEL:SET BACK:EXIT");
 }else{
  text(bitmap,1,56,"SET M");number(bitmap,31,56,per_selected+1,per_selected>=9?2:1);line(bitmap,0,53,128);
  number(bitmap,59,56,per_amounts[per_selected],3);line(bitmap,82,59,42);
  u32 thumb=82+per_amounts[per_selected]*41/127;for(u32 yy=57;yy<62;yy++)pixel(bitmap,thumb,yy);
  for(u32 j=0;j<4;j++){
   volatile Route *r=&per_routes[per_selected][j];u32 y=43-j*10;
   number(bitmap,1,y,j+1,1);if(r->track==6)text(bitmap,13,y,"FX");else{text(bitmap,13,y,"T");number(bitmap,19,y,r->track+1,1);}
   text(bitmap,31,y,r->pad?"INVALID":per_param_name_for(per_profile_for_track(r->track),r->track,r->dest));
   glyph(bitmap,79,y,r->depth<0?'-':'+');number(bitmap,85,y,r->depth<0?-r->depth:r->depth,3);

   if(j==per_route)invert(bitmap,0,y-1,128,9);
  }
  small_text(bitmap,0,6,"PIT:ROW DEC:TRK COL:DEST SHP:DEP");
  small_text(bitmap,0,0,per_clip_notice?per_clip_message():"MAIN:AMOUNT LEVEL:M BACK:PERF");
 }
}

extern void per_config_stock(void*);
extern void per_click_label(void);
__asm__(".text\n.globl per_click_label\nper_click_label:\n move.l %a0,-(%sp)\n jsr per_click_label_out\n addq.l #4,%sp\n rts\n");
void per_click_label_out(void *out){u32 allocator=0;CALL(0x400f980c,void(*)(void*,const char*,void*))(out,"CLICK",&allocator);}
void per_click_open(void *capture){
 void *parent=**(void***)capture;
 void *object=CALL(0x40080064,void*(*)(u32))(0x250);
 if(!object)return;
 CALL(0x4002784a,void(*)(void*))(object);

 u32 *base=(u32*)((u8*)object+0x38);u32 *begin=(u32*)base[7],*end=(u32*)base[8],*write=begin;
 for(u32 *read=begin;read!=end;read++)if(*read!=2)*write++=*read;
 base[8]=(u32)write;
 u32 *control=CALL(0x40080064,u32*(*)(u32))(16);

 control[0]=0x401000fc;control[1]=1;control[2]=1;control[3]=(u32)object;
 u32 shared[2]={(u32)object+0x38,(u32)control};
 CALL(0x40075754,void(*)(void*,void*))(parent,shared);
 CALL(0x400cf23c,void(*)(void*))(shared+1);
}

/* Les libelles natifs renvoient la chaine par A0 ; ABI C preservee. */
extern void per_macros_label(void),per_reload_label(void);
__asm__(".text\n.globl per_macros_label\nper_macros_label:\n move.l %a0,-(%sp)\n jsr per_macros_label_out\n addq.l #4,%sp\n rts\n"
        ".globl per_reload_label\nper_reload_label:\n move.l %a0,-(%sp)\n jsr per_reload_label_out\n addq.l #4,%sp\n rts\n");
void per_macros_label_out(void *out){u32 allocator=0;CALL(0x400f980c,void(*)(void*,const char*,void*))(out,"MACROS",&allocator);}
void per_reload_label_out(void *out){u32 allocator=0;CALL(0x400f980c,void(*)(void*,const char*,void*))(out,per_reload_keep?"RLD: ON":"RLD: OFF",&allocator);}
static void per_menu_item(void *parent,void (*label_fn)(void),void (*action_fn)(void*)){
 u32 *label_capture=CALL(0x40080064,u32*(*)(u32))(1);
 u32 *action_capture=CALL(0x40080064,u32*(*)(u32))(4);*action_capture=(u32)parent;
 u32 label[4]={(u32)label_capture,0,0x4003b30e,(u32)label_fn};
 u32 action[4]={(u32)action_capture,0,0x4003b360,(u32)action_fn};
 u32 empty[4]={0};
 void *item=CALL(0x40080064,void*(*)(u32))(0x54);
 CALL(0x400734b0,void(*)(void*,void*,void*,void*,void*,u32,u32))(item,label,action,empty,empty,0xffffffff,8);
 CALL(0x40072ce6,void(*)(void*,void*))(parent,item);
 CALL(0x400cf044,void(*)(void*))(action);CALL(0x400cf044,void(*)(void*))(label);
}
void per_reload_toggle(void *capture){
 void *parent=**(void***)capture;
 per_reload_keep=!per_reload_keep;
 CALL(0x40076082,void(*)(void*))((u8*)parent+0x38);
}
/* Sortie partagee par A0 ; le natif attache le retour BACK au parent. */
extern void per_menu_share(u32*,void*,void*);
__asm__(".text\n.globl per_menu_share\nper_menu_share:\n move.l 4(%sp),%a0\n move.l 12(%sp),-(%sp)\n move.l 12(%sp),-(%sp)\n jsr 0x4007536a\n addq.l #8,%sp\n rts\n");
void per_macros_open(void *capture){
 void *parent=**(void***)capture;
 void *object=CALL(0x40080064,void*(*)(u32))(0x23c);
 if(!object)return;
 u32 title=0,allocator=0;
 CALL(0x400f980c,void(*)(void*,const char*,void*))(&title,"MACROS",&allocator);

 CALL(0x400406d8,void(*)(void*,const char*,u32,void*,u32))(object,"PerformanceMacroSettings",4,&title,0x40fe39a0);
 CALL(0x400f7d5c,void(*)(void*))(&title);
 per_menu_item(object,per_reload_label,per_reload_toggle);
 u32 shared[2];per_menu_share(shared,parent,(u8*)object+0x38);
 CALL(0x40075754,void(*)(void*,void*))(parent,shared);
 CALL(0x400cf23c,void(*)(void*))(shared+1);
}
void per_config(void *parent){
 per_config_stock(parent);
 per_menu_item(parent,per_click_label,per_click_open);
 per_menu_item(parent,per_macros_label,per_macros_open);
}

extern u32 per_root_encoder_stock(void*,void*);
u32 per_root_encoder(void *root,void *event){
 if(!per_ui_state_ok())return 1;
 if(per_mode&&((u32*)event)[3]==16){
  if(!blocked()&&!key(2)&&!key(3)&&!key(4)){
   s32 change=delta(event);
   if(change){u32 m=per_mode==2?per_selected:4;if(per_mode==1)per_selected=4;per_amounts[m]=clamp((s32)per_amounts[m]+change,0,127);per_storage_edit();per_refresh(mask(m));if(per_main_view)invalidate((void*)per_main_view);}
  }
  return 1;
 }
 return per_root_encoder_stock(root,event);
}

volatile u32 per_power_owned DATA=0,per_power_macro DATA=0;
void per_power(void *root,u32 pressed){
 per_ui_state_ok();
 if(pressed){
  if(!per_power_owned&&per_mode&&per_main_view&&!*((u8*)per_main_view+0x17)&&!blocked()&&!key(1)&&!key(2)&&!key(3)&&!key(4)){
   per_power_owned=1;per_power_macro=per_selected;
  }
  CALL(0x4000637a,void(*)(void*,u32))(root,pressed);return;
 }
 void *notification=*(void**)((u8*)root+0xe4);
 u32 reset=per_power_owned&&per_mode&&per_main_view&&!*((u8*)per_main_view+0x17)&&notification&&!*((u8*)notification+0x20)&&!blocked();
 u32 m=per_power_macro;per_power_owned=0;
 CALL(0x4000637a,void(*)(void*,u32))(root,pressed);
 if(reset&&m<15){per_amounts[m]=0;per_storage_edit();per_refresh(mask(m));invalidate((void*)per_main_view);}
}
