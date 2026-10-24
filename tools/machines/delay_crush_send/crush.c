/* Routage prive : dry/wet historique ou remplacement direct en sortie du mixeur.
 * Aucun E/S, allocation, flottant ou division64 dans le bloc audio. */
typedef unsigned int u32;typedef int s32;typedef short s16;
extern volatile u32 cr_mode,cr_rate,cr_bits,cr_send[6],cr_side,cr_side_on;
#ifndef CR_LEAN_FX
static s32 direct_bus[64],echo_bus[64],delay_bus[64];
static u32 echo_nonzero;
#endif
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
 struct cr_state *s=&cr_state;u32 wanted=cr_mode<
#ifdef CR_LEAN_FX
3
#else
5
#endif
?cr_mode:0;
 if(!s->ready){s->ready=1;s->gain=256;s->prior_gain=256;}
 if(wanted!=s->active){if(s->gain>=8)s->gain-=8;else s->gain=0;if(!s->gain){s->active=wanted;s->echo=(struct quant_state){0};s->direct=(struct quant_state){0};}}
 else if(s->gain<256)s->gain+=8;
 s->delta_enabled=s->active==2
#ifndef CR_LEAN_FX
 ||s->active==4
#endif
 ;
 if(s->delta_enabled){
  const s32 *direct=
#ifdef CR_LEAN_FX
in;
#else
s->active==4?direct_bus:in;
#endif
  crush(&s->direct,s->delta,direct,cr_rate,cr_bits);
  for(u32 i=0;i<32;i++){s32 gain=(s32)s->prior_gain+(((s32)s->gain-(s32)s->prior_gain)*(s32)(i+1)>>5);
   for(u32 c=0;c<2;c++){u32 j=2*i+c;s32 d=(s->delta[j]>>11)-(
#ifdef CR_LEAN_FX
undo_send(in[j]>>11)
#else
s->active==4?(direct[j]>>11):undo_send(in[j]>>11)
#endif
);s->delta[j]=((d>>8)*gain)+(((d&255)*gain)>>8);}
  }
 }
 if(s->active==1||s->active==2){
  u32 work=*(volatile u32*)0x8000b570;
  if(work>=0x8000a560&&work<=0x8000b470&&!(work&3))for(u32 i=0;i<64;i++)((volatile s32*)work)[i]=0;
  if(s->active==1)crush(&s->echo,out,in,cr_rate,cr_bits);else for(u32 i=0;i<64;i++)out[i]=0;
 }else{
  const s32 *feed=in;
  #ifndef CR_LEAN_FX
  if(s->active>=3){
   if(echo_nonzero){
    crush(&s->echo,delay_bus,echo_bus,cr_rate,cr_bits);
    for(u32 i=0;i<64;i++)delay_bus[i]=limited((in[i]>>11)+(delay_bus[i]>>11)-(echo_bus[i]>>11));
    feed=delay_bus;
   }else s->echo=(struct quant_state){0};
  }
  #endif
  cr_native(out,feed,params);
 }
 if(s->gain!=256||s->prior_gain!=256){
  for(u32 i=0;i<32;i++){s32 gain=(s32)s->prior_gain+(((s32)s->gain-(s32)s->prior_gain)*(s32)(i+1)>>5);for(u32 c=0;c<2;c++)out[2*i+c]=((out[2*i+c]>>8)*gain);}
 }
 s->prior_gain=s->gain;
}
void cr_post(s32 *mix){struct cr_state *s=&cr_state;if(!s->delta_enabled)return;for(u32 i=0;i<64;i++)mix[i]=limited((mix[i]>>11)+s->delta[i]);s->delta_enabled=0;}

/* Bus distincts par piste. Les gains dry et delay natifs sont lus apres calcul
 * des cibles ; aucun parametre de pattern n'est detourne pour le crusher.
 * Les deux sommes reutilisent le mixeur EMAC natif (32 trames, six pistes).
 * Le direct conserve le mid/side Wizard avant sa conversion stock tardive. */
#ifndef CR_LEAN_FX
static s32 dg[2][6],eg[2][6],left[192],right[192];
static s32 scale(s32 x,u32 amount){return (x>>15)*(s32)amount+(s32)(((u32)x&32767u)*amount>>15);}
static void bus(s32 *out,const s32 *source,s32 *gain,const s32 *target){
 s32 delta[6];for(u32 t=0;t<6;t++)delta[t]=(s32)((u32)target[t]-(u32)gain[t])>>5;
 ((void(*)(s32*,const s32*,s32*,const s32*))0x40056716)(out,source,gain,delta);
}
#ifdef CR_CPU_OPT
/* Memes sources/gains/cibles : une somme native suffit, garder le ramp exact. */
static void paired_bus(s32*out,const s32*ls,const s32*rs,s32 gain[2][6],s32 target[2][6]){
 u32 same=ls==rs;
 for(u32 t=0;t<6&&same;t++)if(gain[0][t]!=gain[1][t]||target[0][t]!=target[1][t])same=0;
 bus(out,ls,gain[0],target[0]);
 if(same){for(u32 i=0;i<32;i++)out[2*i+1]=out[2*i];for(u32 t=0;t<6;t++)gain[1][t]=gain[0][t];}
 else bus(out+1,rs,gain[1],target[1]);
}
#endif
void cr_split(s32 *out,const s32 *in,const s16 *params,const s32 *dl,const s32 *dr){
 u32 wanted=cr_mode<5?cr_mode:0,active=cr_state.active;
 if(wanted>=3||active>=3){
  s32 dt[2][6],et[2][6];u32 direct=active==4||wanted==4;
  const s32 *mid=(const s32*)0x80001858;const u32 *on=(const u32*)cr_side_on;const s32 *side=(const s32*)cr_side;
  echo_nonzero=0;
  for(u32 t=0;t<6;t++){
   u32 v=cr_send[t];if(v>127)v=127;u32 amount=v*v*32768u/16129u;
   for(u32 c=0;c<2;c++){
    s32 dry=((const s32*)(c?0x40a78be8:0x40a78c08))[t];
    dry=(s32)((u32)dry+((u32)(c?dr:dl)[t]<<5));
    if(dry>0||(*(volatile unsigned char*)0x404e9b53&(1u<<t)))dry=0;
    s32 echo=((const s32*)(c?0x40a78bb8:0x40a78bd0))[t];if(echo>0)echo=0;
    dt[c][t]=direct?scale(dry,amount):0;et[c][t]=scale(echo,amount);
    if(et[c][t]||eg[c][t])echo_nonzero=1;
   }
#ifndef CR_CPU_OPT
   if(direct)for(u32 i=0;i<32;i++){
    u32 j=32*t+i;s32 m=mid[j],sd=side&&on&&on[t]?side[j]:0;
    left[j]=sd?limited((m>>11)+(sd>>11)):m;right[j]=sd?limited((m>>11)-(sd>>11)):m;
   }
#endif
  }
#ifdef CR_CPU_OPT
  if(echo_nonzero)paired_bus(echo_bus,mid,mid,eg,et);
  if(direct){
   u32 stereo=0;if(side&&on)for(u32 t=0;t<6;t++)stereo|=on[t];
   if(stereo){
    for(u32 t=0;t<6;t++)for(u32 i=0;i<32;i++){
     u32 j=32*t+i;s32 m=mid[j],sd=on[t]?side[j]:0;
     left[j]=sd?limited((m>>11)+(sd>>11)):m;right[j]=sd?limited((m>>11)-(sd>>11)):m;
    }
    paired_bus(direct_bus,left,right,dg,dt);
   }else paired_bus(direct_bus,mid,mid,dg,dt);
  }
#else
  if(echo_nonzero){bus(echo_bus,mid,eg[0],et[0]);bus(echo_bus+1,mid,eg[1],et[1]);}
  if(direct){bus(direct_bus,left,dg[0],dt[0]);bus(direct_bus+1,right,dg[1],dt[1]);}
#endif
  else for(u32 c=0;c<2;c++)for(u32 t=0;t<6;t++)dg[c][t]=0;
 }else{
  for(u32 c=0;c<2;c++)for(u32 t=0;t<6;t++){dg[c][t]=0;eg[c][t]=0;}
  echo_nonzero=0;
 }
 cr_process(out,in,params);
}

#else
void cr_split(s32*out,const s32*in,const s16*params,const s32*dl,const s32*dr){(void)dl;(void)dr;cr_process(out,in,params);}
#endif
