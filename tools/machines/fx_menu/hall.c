/* HALL original,12kHz : quatre combs amortis et deux diffuseurs par canal.
 * Rings PS1 reutilises exclusivement, aucun buffer ni resampling dynamique.
 * Delais plus longs que ROOM pour une queue large avec un cout borne. */
#include "fx.h"
extern s16 ps_comb[2][4][2056],ps_ap[2][1024];
static u32 hall_w,hall_fill,hall_pos[2][2],hall_apfill[2][2],hall_decay,hall_tone;
static s32 hall_low[2][4],hall_previous[2];
#ifdef FX_POLISH
static s32 hall_error[2][4];
#endif
static s32 hs(s32 x){return x>32767?32767:x< -32768?-32768:x;}
void fx_hall_reset(void){
 hall_w=hall_fill=hall_decay=hall_tone=0;
 for(u32 c=0;c<2;c++){hall_previous[c]=0;for(u32 k=0;k<4;k++){hall_low[c][k]=0;
#ifdef FX_POLISH
hall_error[c][k]=0;
#endif
}for(u32 k=0;k<2;k++)hall_pos[c][k]=hall_apfill[c][k]=0;}
}
void fx_hall(s32*out,const s32*in,const s16*params){
 static const u32 length[4]={659,827,997,1217},cross[4]={19,37,53,71};
 u32 size=params[0]<0?0:(u32)params[0]>>8,tone=params[1]<0?0:(u32)params[1]>>8;
 if(size>127)size=127;if(tone>127)tone=127;
 u32 decay=12288+size*19328/127,damp=2048+tone*26624/127;
#ifdef FX_POLISH
 /* INF : boucle quasi figee, strictement sous l unite ; autres tailles identiques. */
 if(size==127)decay=32640;
#endif
 if(!hall_fill){hall_decay=decay;hall_tone=damp;}
 else{hall_decay=(u32)((s32)hall_decay+(((s32)decay-(s32)hall_decay)>>5));hall_tone=(u32)((s32)hall_tone+(((s32)damp-(s32)hall_tone)>>5));}
 for(u32 i=0;i<32;i+=4){
  for(u32 c=0;c<2;c++){
   s32 input=(in[2*i+c]>>18)+(in[2*(i+1)+c]>>18)+(in[2*(i+2)+c]>>18)+(in[2*(i+3)+c]>>18),sum=0;
   for(u32 k=0;k<4;k++){
    u32 n=length[k]+c*cross[k];s32 old=hall_fill<n?0:ps_comb[c][k][(hall_w-n)&2047];sum+=old;
    s32 low;
#ifdef FX_POLISH
    /* Reste fractionnaire conserve : pas de DC ni de blocage sous un LSB. */
    s32 change=(old-hall_low[c][k])*(s32)hall_tone+hall_error[c][k];
    low=hall_low[c][k]+(change>>15);hall_error[c][k]=change&32767;
#else
    low=hall_low[c][k]+(((old-hall_low[c][k])*(s32)hall_tone)>>15);
#endif
    if(!input&&low>-2&&low<2)low=0;hall_low[c][k]=low;
    ps_comb[c][k][hall_w]=(s16)hs((input>>1)+
#ifdef FX_POLISH
    /* Troncature symetrique : une boucle silencieuse rejoint vraiment zero. */
    (low*(s32)hall_decay)/32768
#else
    ((low*(s32)hall_decay)>>15)
#endif
    );
   }
   s32 y=sum/4;
   for(u32 k=0;k<2;k++){
    u32 p=hall_pos[c][k],n=(k?211:149)+c*(k?23:17),at=k*512+p;
    s32 z=hall_apfill[c][k]<n?0:ps_ap[c][at],x=y;y=hs(z-(x>>1));ps_ap[c][at]=(s16)hs(x+(y>>1));
    hall_pos[c][k]=p+1==n?0:p+1;if(hall_apfill[c][k]<n)hall_apfill[c][k]++;
   }
   s32 previous=hall_previous[c];for(u32 j=0;j<4;j++)out[2*(i+j)+c]=(previous+(y-previous)*(s32)(j+1)/4)*65536;hall_previous[c]=y;
  }
  hall_w=(hall_w+1)&2047;if(hall_fill<2048)hall_fill++;
 }
}
