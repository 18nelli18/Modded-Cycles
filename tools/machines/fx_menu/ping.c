#include "fx.h"
/* v80 : Delay/Crush natifs et Ping Pong seulement. Aucun pitch ni ring prive.
 * La commutation et son fondu gardent exactement les paliers anterieurs. */
extern void fx_legacy_split(s32*,const s32*,const s16*,const s32*,const s32*);
extern u32 fx_delay_state[];
static s32 nd_feed[64];
static u32 nd_active,nd_ready,nd_gain,nd_prior;
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
 if(wanted!=nd_active){nd_gain=nd_gain>=8?nd_gain-8:0;if(!nd_gain)nd_active=wanted;}
 else if(nd_gain<256)nd_gain+=8;
 if(!nd_active)fx_legacy_split(out,in,params,dl,dr);
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
