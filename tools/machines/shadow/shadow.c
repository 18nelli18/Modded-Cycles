/* Shadow : synthese pulsar originale, inspiree du principe de Dust (Fors).
 * Trois trains de grains fenetres, arithmetique32bits et VCA/gate natifs.
 * Pas de code, echantillon ou preset extrait du plugin. */
typedef int s32;typedef unsigned int u32;typedef short s16;typedef signed char s8;
#include "shadow_tables.h"
typedef struct {u32 phase[3],grain[3],ginc[3],rng[3],live[3],age;} State;
typedef struct {s32 note,grain,density,spread,chaos,punch,trig;} Input;
struct Track{State state;Input in;};struct Track shadow_tracks[6];
const char shadow_name[]="Shadow";
const char shadow_labels[5][8]={"Grain","Density","Spread","Chaos","Decay"};
const char shadow_short_labels[5][8]={"GRN","DENS","SPRD","CHAO","DEC"};
const u32 shadow_state_bytes=sizeof(State),shadow_input_bytes=sizeof(Input),shadow_track_bytes=sizeof(struct Track);
static s32 clip(s32 x,s32 lo,s32 hi){return x<lo?lo:x>hi?hi:x;}
static u32 random_next(u32 x){x^=x<<13;x^=x>>17;x^=x<<5;return x;}
static void reset(State*s){for(u32 j=0;j<3;j++){s->phase[j]=0xffffffffu;s->grain[j]=s->ginc[j]=s->live[j]=0;s->rng[j]=0x6d2b79f5u+j*0x1234567u;}s->age=0;}
void shadow_block(State*s,const Input*in,s32*out){
 if(in->trig)reset(s);s32 note=clip(in->note,0,127<<16),index=note>>16;
 u32 inc=SH_INC[index]+(((SH_INC[index+1]-SH_INC[index])>>10)*((u32)(note&65535)>>6));
 u32 spread=clip(in->spread,0,127),density=8+((u32)clip(in->density,0,127)*120>>7),chaos=clip(in->chaos,0,127),ratio=1+((u32)clip(in->grain,0,127)>>3);
 u32 detune=(inc>>8)*spread,incs[3]={inc,inc+detune,inc-(detune>>1)},n=spread?3:1;
 for(u32 i=0;i<32;i++){
  s32 sum=0;
  for(u32 j=0;j<n;j++){
   u32 before=s->phase[j];s->phase[j]+=incs[j];
   if(s->phase[j]<before){u32 r=random_next(s->rng[j]);s->rng[j]=r;s->grain[j]=0;s->live[j]=(r&127)<=density;
    u32 base=incs[j]>(0x60000000u/ratio)?0x60000000u:incs[j]*ratio;
    s32 offset=((s32)((r>>16)&255)-128)*(s32)chaos/128;
    s->ginc[j]=(u32)((s32)base+(s32)(base>>8)*offset);
   }
   if(s->live[j]){u32 phase=s->grain[j],ix=phase>>24,window=ix<128?ix:255-ix; s32 wave=((s32)SH_SINE[ix]*(s32)window)>>7;
    sum+=j?(wave*(s32)spread)>>7:wave;
    s->grain[j]+=s->ginc[j];if(s->grain[j]<phase)s->live[j]=0;
   }
  }
  if(in->punch&&s->age<384){u32 x=s->age&127;sum=(sum*(s32)(127-x))>>7;}
  out[i]=sum*4096;s->age++;
 }
}
#define V32(o) (*(s32*)(v+(o)))
#define P16(o) (*(const s16*)(p+(o)))
static struct Track*track(char*v){return &shadow_tracks[((u32)v-0x42308828u)/0x31c];}
void shadow_update(s32 pmod,char*v,const char*p){struct Track*t=track(v);if(V32(0x2c)!=0x53484431){reset(&t->state);V32(0x2c)=0x53484431;}
 s32 dec=clip((s8)p[0x24],0,127);V32(0x250)=((const s32*)0x4011d84c)[dec];
 if(V32(0x38)){V32(0x274)=V32(0x278)=0x012c0f26;V32(0x280)=V32(0x284)=0x001f7c5c;V32(0x290)=V32(0x294)=0x7fffffff;V32(0x27c)=(s32)0x82581e4bu;V32(0x288)=(s32)0x803ef8b8u;V32(0x29c)=0x7fffffff;V32(0x2a0)=V32(0x2a4)=0x20000000;V32(0x48)=0;}
 t->in.note=clip((s32)P16(0x14)*256-(64<<16)+pmod+((s32)P16(0x22)-0x4000)*2,0,127<<16);
 t->in.grain=clip(P16(0x16)>>8,0,127);t->in.density=clip(P16(0x18)>>8,0,127);t->in.spread=clip(P16(0x1a)>>8,0,127);t->in.chaos=clip(P16(0x1c)>>8,0,127);t->in.punch=P16(0x1e)!=0;t->in.trig=V32(0x38)!=0;
}
void shadow_render(s32*out,char*v){struct Track*t=track(v);u32 a=V32(0x230)<0?0u-(u32)V32(0x230):(u32)V32(0x230),b=V32(0x234)<0?0u-(u32)V32(0x234):(u32)V32(0x234);
 if(!V32(0x34)&&!V32(0x38)&&a<(1<<14)&&b<(1<<14)){for(s32 i=0;i<32;i++)out[i]=0;return;}
 shadow_block(&t->state,&t->in,out);((void(*)(char*))0x400a9252)(v);((void(*)(s32*,char*))0x400a9430)(out,v);
}
