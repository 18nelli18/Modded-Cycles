#include "fx.h"
/* v80 : Delay/Crush natifs et Ping Pong seulement. Aucun pitch ni ring prive.
 * La commutation et son fondu gardent exactement les paliers anterieurs. */
extern void fx_legacy_split(s32*,const s32*,const s16*,const s32*,const s32*);
extern u32 fx_delay_state[];
static s32 nd_feed[64];
static u32 nd_active,nd_ready,nd_gain,nd_prior;
#ifdef FX_DUCK
static u32 duck_env,duck_gain=32768;
static s32 duck_scale(s32 x,u32 g){return (x>>15)*(s32)g+(s32)(((u32)x&32767u)*g>>15);}
static void duck_wet(s32*out,const s32*in){
 u32 amount=fx_duck_amount<128?fx_duck_amount:127,release=fx_duck_release<128?fx_duck_release:127;
 if(!amount&&duck_gain==32768){duck_env=0;return;}
 u32 peak=0;for(u32 i=0;i<64;i++){s32 x=in[i];u32 a=(x<0?0u-(u32)x:(u32)x)>>16;if(a>peak)peak=a;}
#ifdef FX_EXTRA
 /* Seuil plus sensible et hold/recovery : les attaques cachent franchement
  * les echos, qui remontent entre les phrases sans changer leur feedback. */
 if(peak>16)duck_env=48+release*3;
 else if(duck_env)duck_env--;
 u32 wet=duck_env?256:32768;
 u32 target=32768-((32768-wet)*amount/127u);
 if(target>duck_gain){u32 n=48+release*6;target=duck_gain+(target-duck_gain+n-1)/n;}
#else
 u32 blocks=32+release*4;if(peak>=duck_env)duck_env=peak;else duck_env-=(duck_env-peak+blocks-1)/blocks;
 u32 wet=16777216u/(512+duck_env);if(wet<4096)wet=4096;
 u32 target=32768-((32768-wet)*amount>>7);
#endif
 s32 delta=(s32)target-(s32)duck_gain;
 for(u32 i=0;i<32;i++){u32 g=(u32)((s32)duck_gain+((delta*(s32)(i+1))>>5));out[2*i]=duck_scale(out[2*i],g);out[2*i+1]=duck_scale(out[2*i+1],g);}
 duck_gain=target;
}
#endif
void fx_delay_return(s32*work){
 if(nd_active==5
#ifdef FX_DUB_DISTINCT
 ||nd_active==9
#endif
 )for(u32 i=0;i<32;i++){s32 x=work[2*i];work[2*i]=work[2*i+1];work[2*i+1]=x;}
}
void fx_delay(s32*out,const s32*in,const s16*params,const s32*dl,const s32*dr){
 u32 wanted=FX_SPECIAL_DELAY(cr_mode)?cr_mode:0;
 if(!nd_ready){nd_ready=1;nd_gain=nd_prior=256;}
 if(wanted!=nd_active){nd_gain=nd_gain>=8?nd_gain-8:0;if(!nd_gain){nd_active=wanted;
#ifdef FX_DUCK
 duck_env=0;duck_gain=32768;
#ifdef FX_EXTRA
 fx_extra_reset(1);
#endif
#endif
 }}
 else if(nd_gain<256)nd_gain+=8;
 if(!nd_active)fx_legacy_split(out,in,params,dl,dr);
#ifdef FX_DUCK
#ifdef FX_EXTRA
 else if(nd_active==11){fx_delay_state[4]=0;fx_phaser(out,in);}
#endif
 else if(nd_active==10){fx_delay_state[4]=0;((void(*)(s32*,const s32*,const s16*))0x40057488)(out,in,params);duck_wet(out,in);}
#endif
#if defined(FX_CHEAP)&&!defined(FX_DUB_DISTINCT)
 else if(nd_active==9){fx_delay_state[4]=0;((void(*)(s32*,const s32*,const s16*))0x40057488)(out,in,params);}
#endif
 else{
  if(*(volatile u32*)0x8000b570==0x8000b590){
   for(u32 i=0;i<32;i++){nd_feed[2*i]=(in[2*i]>>1)+(in[2*i+1]>>1);nd_feed[2*i+1]=0;}
  }
  fx_delay_state[4]=0;
  ((void(*)(s32*,const s32*,const s16*))0x40057488)(out,nd_feed,params);
 }
 if(nd_gain!=256||nd_prior!=256)for(u32 i=0;i<32;i++){
  s32 g=(s32)nd_prior+(((s32)nd_gain-(s32)nd_prior)*(s32)(i+1)>>5);
  for(u32 c=0;c<2;c++)out[2*i+c]=((out[2*i+c]>>8)*g);
 }
 nd_prior=nd_gain;
}
