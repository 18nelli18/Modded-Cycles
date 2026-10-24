/* Chorus stereo original, inspire BBD : deux delais modules opposes.
 * Q20 audio, interpolation lineaire8bits, filtres doux et saturation cubique.
 * Aucun acces UI/disque, allocation, division ou calcul64bits dans le rendu.
 */
typedef unsigned int u32; typedef int s32; typedef short s16;
extern volatile u32 ch_mode;
extern void ch_native(s32*,const s32*,const s16*);
#include "sine.h"
struct ch_state {s32 ring[2][1024],pre[2],post[2],delay[2];u32 write,phase,drift,active,gain,ready,filled,prior_gain;};
struct ch_state ch_state;
static s32 clip(s32 x){return x>1048575?1048575:x< -1048575?-1048575:x;}
static s32 sine(u32 p){u32 i=p>>24,f=(p>>16)&255;return CH_SINE[i]+(((CH_SINE[(i+1)&255]-CH_SINE[i])*(s32)f)>>8);}
static s32 sample(u32 c,u32 w,s32 d){u32 p=(w<<16)-(u32)d,i=(p>>16)&1023,f=(p>>8)&255;s32 a=ch_state.ring[c][i],b=ch_state.ring[c][(i+1)&1023];return a+(((b-a)*(s32)f)>>8);}
void ch_chorus(s32 *out,const s32 *in,const s16 *params,u32 mode,u32 gain){
 struct ch_state *s=&ch_state;s32 speed=params[0],depth=params[1];
 if(speed<0)speed=0;if(speed>32512)speed=32512;if(depth<0)depth=0;if(depth>32512)depth=32512;
 u32 inc=(mode==2?858993u:429497u)+(((u32)speed*(mode==2?57266u:28633u))>>8);
 s32 amp=(depth*(mode==2?387:242))>>8,mod=(amp*sine(s->phase))>>7;
 s32 drift=sine(s->drift)*2,target[2]={(432<<16)+mod+drift,(432<<16)-mod-drift},step[2];
 if(!s->delay[0]){s->delay[0]=target[0];s->delay[1]=target[1];}
 for(u32 c=0;c<2;c++)step[c]=(target[c]-s->delay[c])>>5;
 s->phase+=inc;s->drift+=171799u;
 s32 ramp=(s32)gain-(s32)s->prior_gain;u32 smooth=gain<256||ramp;
 for(u32 i=0;i<32;i++){
  u32 g=(u32)((s32)s->prior_gain+((ramp*(s32)(i+1))>>5));
  if(s->filled<1024)s->filled++;
  for(u32 c=0;c<2;c++){
   s32 x=in[i*2+c]>>11;s->pre[c]+=(x-s->pre[c])>>1;if(!x&&s->pre[c]>=-1&&s->pre[c]<=1)s->pre[c]=0;
   s32 small=s->pre[c]>>10;s32 sat=s->pre[c]-((small*small*small)>>13);
   s->ring[c][s->write]=clip(sat);s32 wet=(s->filled<1024&&(((u32)s->delay[c]+65535)>>16)>=s->filled)?0:sample(c,s->write,s->delay[c]);
   s->post[c]+=(wet-s->post[c])>>1;if(!wet&&s->post[c]>=-1&&s->post[c]<=1)s->post[c]=0;wet=s->post[c];
   if(smooth)wet=(wet*(s32)g)>>8;
   out[i*2+c]=wet*2048; /* Retour wet SEUL : le mixeur ajoute ensuite le dry. */s->delay[c]+=step[c];
  }
  s->write=(s->write+1)&1023;
 }
 s->prior_gain=gain;
}
void ch_process(s32 *out,const s32 *in,const s16 *params){
 struct ch_state *s=&ch_state;u32 wanted=ch_mode<3?ch_mode:0;
 if(!s->ready){s->ready=1;s->gain=256;}
 /* Fondu21ms par cote du changement, sans calcul simultane des deux FX. */
 if(wanted!=s->active){if(s->gain>=8)s->gain-=8;else s->gain=0;if(!s->gain){if(!s->active&&wanted){s->filled=s->write=0;s->pre[0]=s->pre[1]=s->post[0]=s->post[1]=0;}s->active=wanted;s->delay[0]=s->delay[1]=0;}}
 else if(s->gain<256)s->gain+=8;
 if(s->active){ch_chorus(out,in,params,s->active,s->gain);return;}
 if(s->gain==256){ch_native(out,in,params);s->prior_gain=256;return;}
 ch_native(out,in,params);
 for(u32 i=0;i<64;i++){
  u32 g=(u32)((s32)s->prior_gain+(((s32)s->gain-(s32)s->prior_gain)*(s32)(i/2+1)>>5));
  out[i]=(((out[i]>>11)*(s32)g)>>8)*2048;
 }
 s->prior_gain=s->gain;
}
