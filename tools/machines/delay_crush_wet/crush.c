/* Routage prive : dry/wet historique ou remplacement direct en sortie du mixeur.
 * Aucun E/S, allocation, flottant ou division64 dans le bloc audio. */
typedef unsigned int u32;typedef int s32;typedef short s16;
extern volatile u32 cr_mode,cr_rate,cr_bits;
extern void cr_native(s32*,const s32*,const s16*);
#include "rates.h"
struct quant_state {u32 phase,increment,bits,envelope; s32 held[2];};
struct cr_state {u32 ready,active,gain,prior_gain,delta_enabled;struct quant_state echo,direct;s32 delta[64];};
struct cr_state cr_state;
static u32 magnitude(s32 x){u32 v=x<0?0u-(u32)x:(u32)x;return v>2147483647u?2147483647u:v;}
static s32 quant(s32 x,u32 step,u32 levels){
 u32 mag=magnitude(x),n=(mag+step/2)/step;if(n>levels)n=levels;mag=n*step;return x<0?-(s32)mag:(s32)mag;
}
static void crush(struct quant_state *s,s32 *out,const s32 *in,u32 rate,u32 bits){
 if(rate>127)rate=127;if(bits<2)bits=2;if(bits>16)bits=16;
 u32 target=CR_RATE[rate],btarget=bits<<8,peak=0;
 for(u32 i=0;i<64;i++){u32 a=magnitude(in[i]);if(a>peak)peak=a;}
 u32 release=s->envelope>>6;if(!release&&s->envelope)release=1;s->envelope-=release;if(peak>s->envelope)s->envelope=peak;
 if(!s->increment){s->increment=target;s->bits=btarget;s->phase=65536;}
 else{int change=(int)target-(int)s->increment;s->increment+=(change>=-8&&change<=8)?change:change/8;
  if(s->bits<btarget)s->bits+=s->bits+8>btarget?btarget-s->bits:8;
  else if(s->bits>btarget)s->bits-=s->bits-btarget<8?s->bits-btarget:8;
 }
 u32 whole=s->bits>>8,frac=s->bits&255,levels=(1u<<(whole-1))-1,step=s->envelope/levels;
 u32 levels2=(1u<<whole)-1,step2=frac?s->envelope/levels2:1;if(!step)step=1;if(!step2)step2=1;
 for(u32 i=0;i<32;i++){
  s->phase+=s->increment;
  if(s->phase>=65536){s->phase&=65535;
   for(u32 c=0;c<2;c++){s32 x=in[2*i+c],a=quant(x,step,levels);if(frac){s32 b=quant(x,step2,levels2);a+=((b-a)>>8)*(s32)frac;}s->held[c]=a;}
  }
  out[2*i]=s->held[0];out[2*i+1]=s->held[1];
 }
}
void cr_crush(s32 *out,const s32 *in,u32 rate,u32 bits){crush(&cr_state.echo,out,in,rate,bits);}
/* Q20 reciproque du gain Send maximal natif (127/128)^2, arrondi.
 * Entrees Q20 : deux produits32 bornes ; aucune multiplication64. */
static s32 undo_send(s32 x){const s32 c=1065154;return ((x>>10)*c>>10)+(((x&1023)*c)>>20);}
static s32 limited(s32 x){if(x>1048575)x=1048575;if(x<-1048576)x=-1048576;return x*2048;}
void cr_process(s32 *out,const s32 *in,const s16 *params){
 struct cr_state *s=&cr_state;u32 wanted=cr_mode<5?cr_mode:0;
 if(!s->ready){s->ready=1;s->gain=256;s->prior_gain=256;}
 if(wanted!=s->active){if(s->gain>=8)s->gain-=8;else s->gain=0;if(!s->gain){s->active=wanted;s->echo=(struct quant_state){0};s->direct=(struct quant_state){0};}}
 else if(s->gain<256)s->gain+=8;
 s->delta_enabled=s->active==2||s->active==4;
 if(s->delta_enabled){
  crush(&s->direct,s->delta,in,cr_rate,cr_bits);
  for(u32 i=0;i<32;i++){s32 gain=(s32)s->prior_gain+(((s32)s->gain-(s32)s->prior_gain)*(s32)(i+1)>>5);
   for(u32 c=0;c<2;c++){u32 j=2*i+c;s32 d=(s->delta[j]>>11)-undo_send(in[j]>>11);s->delta[j]=((d>>8)*gain)+(((d&255)*gain)>>8);}
  }
 }
 if(s->active==1||s->active==2){
  u32 work=*(volatile u32*)0x8000b570;
  if(work>=0x8000a560&&work<=0x8000b470&&!(work&3))for(u32 i=0;i<64;i++)((volatile s32*)work)[i]=0;
  if(s->active==1)crush(&s->echo,out,in,cr_rate,cr_bits);else for(u32 i=0;i<64;i++)out[i]=0;
 }else{cr_native(out,in,params);if(s->active>=3)crush(&s->echo,out,out,cr_rate,cr_bits);}
 if(s->gain!=256||s->prior_gain!=256){
  for(u32 i=0;i<32;i++){s32 gain=(s32)s->prior_gain+(((s32)s->gain-(s32)s->prior_gain)*(s32)(i+1)>>5);for(u32 c=0;c<2;c++)out[2*i+c]=((out[2*i+c]>>8)*gain);}
 }
 s->prior_gain=s->gain;
}
void cr_post(s32 *mix){struct cr_state *s=&cr_state;if(!s->delta_enabled)return;for(u32 i=0;i<64;i++)mix[i]=limited((mix[i]>>11)+s->delta[i]);s->delta_enabled=0;}
