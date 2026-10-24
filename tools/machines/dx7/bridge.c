/* LEGACY : dispatch natif monophonique par piste, controles verrouillables.
 * Les appels OS retournant des pointeurs restent des u32 a la frontiere ABI. */
#include <stdint.h>
typedef uint32_t u32;typedef int32_t s32;typedef int16_t s16;typedef int8_t s8;typedef uint8_t u8;
extern const u8 *dx7_patch(u32);
extern void dx7_note_on(u32,const u8*,s32,u32),dx7_controls(u32,s32,u32,u32,u32,u32),dx7_block(u32,s32*);
extern u32 dx7_is_active(u32);
const char dx7_name[]="LEGACY";
const char dx7_labels[5][8]={"Vel","Voice","Bright","EG Time","Decay"};
const char dx7_short_labels[5][8]={"VEL","VOICE","BRIGHT","EG TIME","DEC"};
static u32 held[6],velocity[6],voice[6];
static s32 clip(s32 x,s32 a,s32 b){return x<a?a:x>b?b:x;}
#define V32(o) (*(s32*)(v+(o)))
#define P16(o) (*(const s16*)(p+(o)))
void dx7_update(s32 pmod,char*v,const char*p){
 u32 lane=((u32)v-0x42308828u)/0x31c;if(lane>=6)return;
 if(V32(0x2c)!=0x4c454731){held[lane]=0;V32(0x2c)=0x4c454731;}
 V32(0x250)=((const s32*)0x4011d84c)[clip((s8)p[0x24],0,127)];
 s32 note=clip((s32)P16(0x14)*256-(64<<16)+pmod+((s32)P16(0x22)-0x4000)*2,0,127<<16);
 u32 vel=clip(P16(0x16)>>8,0,127),patch=clip(P16(0x18)>>8,0,31);
 if(V32(0x38)){
  dx7_note_on(lane,dx7_patch(patch),note,vel);held[lane]=1;velocity[lane]=vel;voice[lane]=patch;
  V32(0x274)=V32(0x278)=0x012c0f26;V32(0x280)=V32(0x284)=0x001f7c5c;V32(0x290)=V32(0x294)=0x7fffffff;
  V32(0x27c)=(s32)0x82581e4bu;V32(0x288)=(s32)0x803ef8b8u;V32(0x29c)=0x7fffffff;
  V32(0x2a0)=V32(0x2a4)=0x20000000;V32(0x48)=0;
 }
 if(V32(0x3c)&&!V32(0x34))held[lane]=0;
 dx7_controls(lane,note,clip(P16(0x1a)>>8,0,127),clip(P16(0x1c)>>8,0,127),64,held[lane]);
}
void dx7_render(s32*out,char*v){
 u32 lane=((u32)v-0x42308828u)/0x31c;
 u32 a=V32(0x230)<0?0u-(u32)V32(0x230):(u32)V32(0x230),b=V32(0x234)<0?0u-(u32)V32(0x234):(u32)V32(0x234);
 if(lane>=6||(!V32(0x34)&&!V32(0x38)&&a<(1<<14)&&b<(1<<14))){for(u32 i=0;i<32;i++)out[i]=0;return;}
 dx7_block(lane,out);if(dx7_is_active(lane))*(volatile u8*)(0x4673205eu+lane)=0;
 ((void(*)(char*))0x400a9252)(v);((void(*)(s32*,char*))0x400a9430)(out,v);
}
extern u32 dx7_previous_popup(u32,u32,u32,s32,u32,u32);
u32 dx7_popup(u32 view,u32 canvas,u32 desc,s32 value,u32 flags,u32 last){
 u32 result=dx7_previous_popup(view,canvas,desc,value,flags,last);if(desc!=147)return result;
 u32 index=clip(value>>8,0,31);char name[11];const u8*p=dx7_patch(index);
 for(u32 i=0;i<10;i++)name[i]=p[145+i]>=32&&p[145+i]<127?p[145+i]:' ';name[10]=0;
 ((void(*)(u32,s32,s32,s32,s32,u32))0x40070efc)(canvas,64,29,127,63,0);
 ((void(*)(u32,u32,s32,s32,u32,const char*,const char*))0x40071a04)(canvas,0x40ea14cc,96,47,2,"%s",name);
 char number[12];((u32(*)(char*,const char*,...))0x40000e6e)(number,"%u",index);
 ((void(*)(u32,u32,s32,s32,u32,const char*,const char*))0x40071a04)(canvas,0x40ea14cc,96,34,2,"%s",number);return result;
}
