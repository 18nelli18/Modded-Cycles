/* Crusher stereo entier, sans allocation ni E/S dans le bloc audio. */
typedef unsigned int u32;typedef int s32;typedef short s16;
extern volatile u32 cr_mode,cr_rate,cr_bits;
extern void cr_native(s32*,const s32*,const s16*);
#include "rates.h"
struct cr_state {u32 phase,ready,active,gain,prior_gain,increment,bits; s32 held[2];};
struct cr_state cr_state;
static s32 quant(s32 x,u32 bits){
 u32 shift=32-bits,mag=x<0?0u-(u32)x:(u32)x;
 if(mag>2147483647u)mag=2147483647u;
 mag=(mag>>shift)<<shift;return x<0?-(s32)mag:(s32)mag;
}
void cr_crush(s32 *out,const s32 *in,u32 rate,u32 bits){
 struct cr_state *s=&cr_state;if(rate>127)rate=127;if(bits<2)bits=2;if(bits>16)bits=16;
 u32 target=CR_RATE[rate],btarget=bits<<8;
 if(!s->increment){s->increment=target;s->bits=btarget;s->phase=65536;}
 else{int change=(int)target-(int)s->increment;s->increment+=(change>=-8&&change<=8)?change:change/8;
  if(s->bits<btarget)s->bits+=s->bits+8>btarget?btarget-s->bits:8;
  else if(s->bits>btarget)s->bits-=s->bits-btarget<8?s->bits-btarget:8;
 }
 u32 whole=s->bits>>8,frac=s->bits&255;
 for(u32 i=0;i<32;i++){
  s->phase+=s->increment;
  if(s->phase>=65536){s->phase&=65535;
   for(u32 c=0;c<2;c++){s32 x=in[2*i+c],a=quant(x,whole);if(frac){s32 b=quant(x,whole+1);a+=((b-a)>>8)*(s32)frac;}s->held[c]=a;}
  }
  out[2*i]=s->held[0];out[2*i+1]=s->held[1];
 }
}
void cr_process(s32 *out,const s32 *in,const s16 *params){
 struct cr_state *s=&cr_state;u32 wanted=cr_mode<3?cr_mode:0;
 if(!s->ready){s->ready=1;s->gain=256;s->prior_gain=256;}
 if(wanted!=s->active){if(s->gain>=8)s->gain-=8;else s->gain=0;if(!s->gain){s->active=wanted;s->increment=0;s->held[0]=s->held[1]=0;}}
 else if(s->gain<256)s->gain+=8;
 if(s->active==1){
  /* Le DMA natif continue a avancer, mais recoit zero feedback en mode Crush.
   * Les anciens echos du ring se drainent ; aucun retour reutilise ne recircule. */
  u32 work=*(volatile u32*)0x8000b570;
  if(work>=0x8000a560&&work<=0x8000b470&&!(work&3))for(u32 i=0;i<64;i++)((volatile s32*)work)[i]=0;
  cr_crush(out,in,cr_rate,cr_bits);
 }else{cr_native(out,in,params);if(s->active==2)cr_crush(out,out,cr_rate,cr_bits);}
 if(s->gain!=256||s->prior_gain!=256){
  for(u32 i=0;i<32;i++){s32 gain=(s32)s->prior_gain+(((s32)s->gain-(s32)s->prior_gain)*(s32)(i+1)>>5);for(u32 c=0;c<2;c++)out[2*i+c]=((out[2*i+c]>>8)*gain);}
 }
 s->prior_gain=s->gain;
}
