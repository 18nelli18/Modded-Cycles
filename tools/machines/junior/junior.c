/* Contrat voix OS1.13 conserve : pitch/fine/decay/gate et VCA natifs.
 * Etat prive par piste, sans allocation ni flottant dans l'interruption audio.
 */
#include "junior_dsp.h"
#define V32(o) (*(s32 *)(v+(o)))
#define P16(o) (*(const s16 *)(p+(o)))
#define MARK 0x4a554e31
struct Track {JuniorState osc;JuniorInput in;};
struct Track junior_tracks[6];
const u32 junior_state_bytes=sizeof(JuniorState);
const u32 junior_input_bytes=sizeof(JuniorInput);
const u32 junior_track_bytes=sizeof(struct Track);
#ifndef JR_NAME
#define JR_NAME "JUNIOR"
#endif
const char junior_name[7]=JR_NAME;
const char junior_short_labels[5][8]={"WAVE","WARP","NOIS","MOTN","DEC"};
const char junior_labels[5][8]={"Wave","Warp","Noise","Motion","Decay"};
static struct Track *track_of(char *v){return &junior_tracks[((u32)v-0x42308828u)/0x31c];}
void junior_update(s32 pmod,char *v,const char *p){
 struct Track *t=track_of(v);
 if(V32(0x2c)!=MARK){junior_reset(&t->osc);V32(0x2c)=MARK;}
 s32 dec=jr_clip((s8)p[0x24],0,127);V32(0x250)=((const s32 *)0x4011d84c)[dec];
 if(V32(0x38)){
  V32(0x274)=V32(0x278)=0x012c0f26;V32(0x280)=V32(0x284)=0x001f7c5c;
  V32(0x290)=V32(0x294)=0x7fffffff;V32(0x27c)=(s32)0x82581e4bu;
  V32(0x288)=(s32)0x803ef8b8u;V32(0x29c)=0x7fffffff;
  V32(0x2a0)=V32(0x2a4)=0x20000000;V32(0x48)=0;
 }
 t->in.note=jr_clip((s32)P16(0x14)*256-(64<<16)+pmod+((s32)P16(0x22)-0x4000)*2,0,127<<16);
 t->in.wave=jr_clip(P16(0x16)>>8,0,127);t->in.warp=jr_clip(P16(0x18)>>8,0,127);
 t->in.noise=jr_clip(P16(0x1a)>>8,0,127);t->in.motion=jr_clip(P16(0x1c)>>8,0,127);
 t->in.punch=P16(0x1e)!=0;t->in.trig=V32(0x38)!=0;
}
void junior_render(s32 *out,char *v){
 struct Track *t=track_of(v);
 u32 a=V32(0x230)<0?0u-(u32)V32(0x230):(u32)V32(0x230);
 u32 b=V32(0x234)<0?0u-(u32)V32(0x234):(u32)V32(0x234);
 if(!V32(0x34)&&!V32(0x38)&&a<(1<<14)&&b<(1<<14)){
  for(s32 i=0;i<32;i++){out[i]=0;} return;
 }
 junior_block(&t->osc,&t->in,out);
 ((void (*)(char *))0x400a9252)(v);
 ((void (*)(s32 *,char *))0x400a9430)(out,v);
}
