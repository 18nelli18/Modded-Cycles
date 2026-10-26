/* SPEAK : banque originale de128mots, synthese formants8kHz, sortie48kHz.
 * Trois resonateurs paralleles ; hauteur et durees phonemes independantes.
 * Aucun code/ROM/echantillon Texas Instruments, aucune allocation audio. */
typedef unsigned int u32;typedef int s32;typedef short s16;typedef unsigned short u16;typedef unsigned char u8;typedef signed char s8;
typedef struct {s16 a1,a2,b;} Resonator;
typedef struct {u16 duration;u8 voice,noise,stop;} Phone;
#include "speak_tables.h"
typedef struct {u32 phase,rng,word,index,remaining,age,done,upsample; s32 last,next,glottal,dc; s32 coef[3][3],hist[3][2];
#ifdef SP_CLEAR
s32 clarity;
#endif
#ifdef SP_SMOOTH
s32 voice_level,noise_level;
#endif
} State;
typedef struct {s32 note,voice,word,speed,artic,punch,trig;} Input;
struct Track {State state;Input in;};struct Track speak_tracks[6];
const char speak_name[]="SPEAK";
const char speak_labels[5][8]={"Voice","Word","Speed","Artic","Decay"};
const char speak_short_labels[5][8]={"VOIC","WORD","SPD","ART","DEC"};
const u32 speak_state_bytes=sizeof(State),speak_input_bytes=sizeof(Input),speak_track_bytes=sizeof(struct Track);
static s32 clip(s32 x,s32 lo,s32 hi){return x<lo?lo:x>hi?hi:x;}
static void reset(State*s,u32 word){
 u32 *p=(u32*)s;for(u32 i=0;i<sizeof(State)/4;i++)p[i]=0;s->word=word;s->rng=0x6d2b79f5u;
}
static s32 sample(State*s,u32 inc,u32 bank,u32 speed,u32 articulation){
 if(s->done)return 0;
 u32 id=SP_WORDS[s->word][s->index];
 if(!s->remaining){
  if(id==255){s->done=1;return 0;}
  s->remaining=(u32)SP_PHONES[id].duration<<8;s->age=0;
 }
 const Phone*p=&SP_PHONES[id];u32 phase=s->phase;s->phase+=inc;
 s->rng^=s->rng<<13;s->rng^=s->rng>>17;s->rng^=s->rng<<5;
 #ifdef SP_TALK
 (void)phase;s->glottal=SP_GLOTTAL[s->phase>>25];
#else
 s32 pulse=s->phase<phase?16384:0;s->glottal+=(pulse-s->glottal)>>1;
#endif
 s->dc+=(s->glottal-s->dc)>>5;
#ifdef SP_SMOOTH
 /* Enveloppes d excitation de2ms : pas de marche brutale au changement
  * voyelle/bruit, a la fin d un S ou apres le burst d une occlusive. */
 s32 vt=(s32)p->voice<<8,nt=(p->stop&&s->age>96)?0:(s32)p->noise<<8;
#ifdef SP_TALK
 if(p->stop)nt=s->age<128?(s32)p->noise*SP_BURST[s->age]:0;
#endif
 s->voice_level+=(vt-s->voice_level)>>4;s->noise_level+=(nt-s->noise_level)>>4;
 s32 voice=(s->glottal-s->dc)*(s->voice_level>>8)>>8;
 s32 noise=((s32)((s->rng>>16)&65535)-32768)*(s->noise_level>>8)>>10;
#else
 s32 voice=(s->glottal-s->dc)*(s32)p->voice>>8;
 s32 noise=((s32)((s->rng>>16)&65535)-32768)*(s32)p->noise>>10;
 if(p->stop&&s->age>96)noise=0;
#endif
 #ifdef SP_TALK
 /* Articulation change les transitions, sans tripler le volume du souffle. */
 noise=noise*(s32)(80+(articulation>>2))>>7;
#else
 noise=noise*(s32)(64+articulation)>>7;
#endif
 s32 x=voice+noise,sum=0;u32 smooth=5-(articulation>>5);
#ifdef SP_SOFT
 /* Formants moins brusques pendant les transitions consonne/voyelle. */
 smooth++;
#endif
#ifdef SP_TALK
 smooth=6-(articulation>>6);
#endif
#ifdef SP_HOT155
/* Trois resonateurs fixes, transitions identiques ; supprimer seulement
 * les compteurs de boucles et les adresses recalculees a8kHz. */
#define SP_RESONATE155(K) do { const Resonator*r=&SP_RESONATORS[bank][id][K]; s->coef[K][0]+=(r->a1-s->coef[K][0])>>smooth; s->coef[K][1]+=(r->a2-s->coef[K][1])>>smooth; s->coef[K][2]+=(r->b-s->coef[K][2])>>smooth; s32 y=((s->coef[K][0]*s->hist[K][0]+s->coef[K][1]*s->hist[K][1])>>14)+((x*s->coef[K][2])>>12); y=clip(y,-24576,24576); s->hist[K][1]=s->hist[K][0]; s->hist[K][0]=y;sum+=y;}while(0)
 SP_RESONATE155(0);SP_RESONATE155(1);SP_RESONATE155(2);
#undef SP_RESONATE155
#else
 for(u32 k=0;k<3;k++){
  const Resonator*r=&SP_RESONATORS[bank][id][k];const s32 target[3]={r->a1,r->a2,r->b};
  for(u32 j=0;j<3;j++)s->coef[k][j]+=(target[j]-s->coef[k][j])>>smooth;
  s32 y=((s->coef[k][0]*s->hist[k][0]+s->coef[k][1]*s->hist[k][1])>>14)+((x*s->coef[k][2])>>12);
  y=clip(y,-24576,24576);s->hist[k][1]=s->hist[k][0];s->hist[k][0]=y;sum+=y;
 }
#endif
 s->age++;
 if(s->remaining<=speed){s->remaining=0;s->index++;}else s->remaining-=speed;
#if defined(SP_CLEAR)&&!defined(SP_SMOOTH)
 /* Accent tres doux des fronts et consonnes, a8kHz : DC inchange,
  * gain maximal1,5 a Nyquist. Etat local a chaque voix. */
 s32 prior=s->clarity;s->clarity=sum;sum+=(sum-prior)>>2;
#endif
 return clip(sum,-32767,32767);
}
#ifdef SP_LEVEL
/* Mise au niveau Q31 du moteur : lineaire pour les syllabes normales,
 * genou continu au-dessus de2048, plafond strict4095 sans wrap signe.
 * A8kHz avant interpolation, jamais de division par sample48kHz. */
static s32 level(s32 x){
 u32 mag=x<0?0u-(u32)x:(u32)x;
 if(mag>2048){u32 excess=mag-2048;mag=2048+excess*2048/(excess+2048);}
 return x<0?-(s32)mag:(s32)mag;
}
#endif
#ifdef SP_HOT155
#define SP_R155 __restrict__
/* Interpolation : |next-last|<=8190, upsample<=5, donc |x|<=40950.
 * floor(x*43691/2^18)+(x<0) == troncature(x/6), sans division. */
static inline s32 interp155(s32 x){return ((x*43691)>>18)+(s32)((u32)x>>31);}
#else
#define SP_R155
#endif
void speak_block(State* SP_R155 s,const Input* SP_R155 in,s32* SP_R155 out){
 if(in->trig)reset(s,(u32)clip(in->word,0,127));
 s32 note=clip(in->note,0,127<<16);u32 n=(u32)note>>16;
 u32 inc=SP_INC[n]+(((SP_INC[n+1]-SP_INC[n])>>10)*((u32)(note&65535)>>6));
 u32 bank=(u32)clip(in->voice,0,127)>>3,speed=64+(u32)clip(in->speed,0,127)*3,art=(u32)clip(in->artic,0,127);
 for(u32 i=0;i<32;i++){
  if(!s->upsample){s->last=s->next;s32 x=sample(s,inc,bank,speed,art);
#ifdef SP_LEVEL
   if(in->punch)x*=2;s->next=level(x);
#else
   s->next=x;
#endif
  }
#if defined(SP_HOT155) && defined(SP_LEVEL)
  s32 v=s->last+interp155((s->next-s->last)*(s32)s->upsample);
#else
  s32 v=s->last+(s->next-s->last)*(s32)s->upsample/6;
#endif
#ifndef SP_LEVEL
  if(in->punch)v=clip(v*2,-32767,32767);
#endif
  out[i]=v*
#ifdef SP_LEVEL
524288
#elif defined(SP_CLEAR)
16384
#else
8192
#endif
;if(++s->upsample==6)s->upsample=0;
 }
}
#define V32(o) (*(s32*)(v+(o)))
#define P16(o) (*(const s16*)(p+(o)))
static struct Track*track(char*v){return &speak_tracks[((u32)v-0x42308828u)/0x31c];}
void speak_update(s32 pmod,char*v,const char*p){struct Track*t=track(v);
 if(V32(0x2c)!=0x53504b31){reset(&t->state,0);t->state.done=1;V32(0x2c)=0x53504b31;}
 s32 dec=clip((s8)p[0x24],0,127);V32(0x250)=((const s32*)0x4011d84c)[dec];
 if(V32(0x38)){V32(0x274)=V32(0x278)=0x012c0f26;V32(0x280)=V32(0x284)=0x001f7c5c;V32(0x290)=V32(0x294)=0x7fffffff;V32(0x27c)=(s32)0x82581e4bu;V32(0x288)=(s32)0x803ef8b8u;V32(0x29c)=0x7fffffff;V32(0x2a0)=V32(0x2a4)=0x20000000;V32(0x48)=0;}
 t->in.note=clip((s32)P16(0x14)*256-(64<<16)+pmod+((s32)P16(0x22)-0x4000)*2,0,127<<16);
 t->in.voice=clip(P16(0x16)>>8,0,127);t->in.word=clip(P16(0x18)>>8,0,127);t->in.speed=clip(P16(0x1a)>>8,0,127);t->in.artic=clip(P16(0x1c)>>8,0,127);t->in.punch=P16(0x1e)!=0;t->in.trig=V32(0x38)!=0;
}
void speak_render(s32*out,char*v){struct Track*t=track(v);u32 a=V32(0x230)<0?0u-(u32)V32(0x230):(u32)V32(0x230),b=V32(0x234)<0?0u-(u32)V32(0x234):(u32)V32(0x234);
 if(!V32(0x34)&&!V32(0x38)&&a<(1<<14)&&b<(1<<14)){for(u32 i=0;i<32;i++)out[i]=0;return;}
 speak_block(&t->state,&t->in,out);
#ifdef SP_SPEED_FIX
 /* Un silence phonemique n est pas une voix terminee. Garder le compteur
  * idle sous son seuil pendant le mot, sans changer stolen/fading/pressure.
  * Une enveloppe eteinte retourne ci-dessus ; un mot fini redevient idle. */
 if(!t->state.done)*(volatile u8*)(0x4673205eu+((u32)v-0x42308828u)/0x31c)=0;
#endif
 ((void(*)(char*))0x400a9252)(v);((void(*)(s32*,char*))0x400a9430)(out,v);
}
extern u32 speak_previous_popup(u32,u32,u32,s32,u32,u32);
u32 speak_popup(u32 view,u32 canvas,u32 desc,s32 value,u32 flags,u32 last){
 u32 result=speak_previous_popup(view,canvas,desc,value,flags,last);if(desc!=142)return result;u32 word=(u32)clip(value>>8,0,127);
 ((void(*)(u32,s32,s32,s32,s32,u32))0x40070efc)(canvas,64,29,127,63,0);
 ((void(*)(u32,u32,s32,s32,u32,const char*,const char*))0x40071a04)(canvas,0x40ea14cc,96,47,2,"%s",SP_NAMES[word]);
 char number[12];((u32(*)(char*,const char*,...))0x40000e6e)(number,"%u",word);
 ((void(*)(u32,u32,s32,s32,u32,const char*,const char*))0x40071a04)(canvas,0x40ea14cc,96,34,2,"%s",number);return result;
}
