/* HALL original,12kHz : quatre combs amortis et deux diffuseurs par canal.
 * Rings PS1 reutilises exclusivement, aucun buffer ni resampling dynamique.
 * Delais plus longs que ROOM pour une queue large avec un cout borne. */
#include "fx.h"
extern s16 ps_comb[2][4][2056],ps_ap[2][1024];
#ifdef HALL_ECO_6K
#define HSTATE extern
#ifdef HALL_ECO_SPARSE
#define HCOMBS 2
#define HAPS 1
#else
#define HCOMBS 4
#define HAPS 2
#endif
#ifdef HALL_ECO_3K
#define HSTEP 16
#define HRING 512
#else
#define HSTEP 8
#define HRING 1024
#endif
#else
#define HSTATE static
#define HCOMBS 4
#define HAPS 2
#define HSTEP 4
#define HRING 2048
#endif
HSTATE u32 hall_w,hall_fill,hall_pos[2][2],hall_apfill[2][2],hall_decay,hall_tone;
HSTATE s32 hall_low[2][4],hall_previous[2];
#ifdef FX_POLISH
HSTATE s32 hall_error[2][4];
#endif
static s32 hs(s32 x){return x>32767?32767:x< -32768?-32768:x;}
#ifndef HALL_ECO_6K
void fx_hall_reset(void){
 hall_w=hall_fill=hall_decay=hall_tone=0;
 for(u32 c=0;c<2;c++){hall_previous[c]=0;for(u32 k=0;k<HCOMBS;k++){hall_low[c][k]=0;
#ifdef FX_POLISH
hall_error[c][k]=0;
#endif
}for(u32 k=0;k<HAPS;k++)hall_pos[c][k]=hall_apfill[c][k]=0;}
}
#endif
void fx_hall(s32*out,const s32*in,const s16*params){
 static const u32 length[4]={659,827,997,1217},cross[4]={19,37,53,71};
 u32 size=params[0]<0?0:(u32)params[0]>>8,tone=params[1]<0?0:(u32)params[1]>>8;
 if(size>127)size=127;if(tone>127)tone=127;
 u32 decay=12288+size*19328/127,damp=2048+tone*26624/127;
#ifdef FX_POLISH
 /* INF : boucle quasi figee, strictement sous l unite ; autres tailles identiques. */
 if(size==127)decay=32640;
#endif
#ifdef HALL_ECO_6K
 /* Deux fois moins de pas, meme attenuation et pole par duree physique. */
 decay=(decay*decay)>>15;
 u32 residual=32768-damp;damp=32768-((residual*residual)>>15);
#ifdef HALL_ECO_3K
 /* Pole exprime par pas ; feedback exprime par tour de ligne, deja conserve. */
 residual=32768-damp;damp=32768-((residual*residual)>>15);
#endif
#endif
 if(!hall_fill){hall_decay=decay;hall_tone=damp;}
 else{hall_decay=(u32)((s32)hall_decay+(((s32)decay-(s32)hall_decay)>>5));hall_tone=(u32)((s32)hall_tone+(((s32)damp-(s32)hall_tone)>>5));}
 for(u32 i=0;i<32;i+=HSTEP){
  for(u32 c=0;c<2;c++){
   s32 input=0,sum=0;
#ifdef HALL_ECO_6K
#ifdef HALL_ECO_3K
   for(u32 j=0;j<16;j++)input+=in[2*(i+j)+c]>>20;
#else
   for(u32 j=0;j<8;j++)input+=in[2*(i+j)+c]>>19;
#endif
#else
   input=(in[2*i+c]>>18)+(in[2*(i+1)+c]>>18)+(in[2*(i+2)+c]>>18)+(in[2*(i+3)+c]>>18);
#endif
   for(u32 k=0;k<HCOMBS;k++){
    u32 n=length[k]+c*cross[k];
#ifdef HALL_ECO_6K
    n=(n+1)>>1;
#ifdef HALL_ECO_3K
    n=(n+1)>>1;
#endif
#endif
    s32 old=hall_fill<n?0:ps_comb[c][k][(hall_w-n)&(HRING-1)];sum+=old;
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
   s32 y=sum/HCOMBS;
   for(u32 k=0;k<HAPS;k++){
    u32 p=hall_pos[c][k],n=(k?211:149)+c*(k?23:17),at=k*512+p;
    #ifdef HALL_ECO_6K
    n=(n+1)>>1;
#ifdef HALL_ECO_3K
    n=(n+1)>>1;
#endif
#endif
    s32 z=hall_apfill[c][k]<n?0:ps_ap[c][at],x=y;y=hs(z-(x>>1));ps_ap[c][at]=(s16)hs(x+(y>>1));
    hall_pos[c][k]=p+1==n?0:p+1;if(hall_apfill[c][k]<n)hall_apfill[c][k]++;
   }
   s32 previous=hall_previous[c];
#ifdef HALL_LINEAR_WET
   /* Garder les fractions du raccord Q31 plutot que rediviser64fois.
    * Dans la zone lineaire seulement : erreur <1LSB de l ancien wet s16,
    * historiques du reseau et extremites de la rampe strictement identiques. */
   if(previous>=-8191&&previous<=8191&&y>=-8191&&y<=8191){
    s32 sample=previous*131072,step=(y-previous)*(131072/HSTEP);
    for(u32 j=0;j<HSTEP;j++){sample+=step;out[2*(i+j)+c]=sample;}
   }else
#endif
#ifdef HALL_RAMP_FAST
#ifdef HALL_MERGED_GAIN
   /* Le genou ne peut etre traverse si les deux extremites sont dans sa
    * region lineaire. Hoister le choix, pas changer la courbe de gain. */
   if(previous>=-8191&&previous<=8191&&y>=-8191&&y<=8191){
    /* Meme troncature vers zero que delta*(j+1)/HSTEP. */
    s32 distance=y-previous,sign=distance>>31;
    u32 magnitude=((u32)distance^(u32)sign)-(u32)sign,phase=0;
    for(u32 j=0;j<HSTEP;j++){
     phase+=magnitude;s32 amount=(s32)(phase/HSTEP);
     s32 v=previous+((amount^sign)-sign);out[2*(i+j)+c]=v*131072;
    }
   }else
#endif
#endif
   for(u32 j=0;j<HSTEP;j++){
    s32 v=previous+(y-previous)*(s32)(j+1)/HSTEP;
#ifdef HALL_MERGED_GAIN
    /* Meme genou que fx_reverb, calcule avant stockage Q31. v reste s16. */
    u32 a=v<0?0u-(u32)v:(u32)v;
    s32 wet=(s32)(a<8192?a*131072u:(24576u+a)*32768u);
    out[2*(i+j)+c]=v<0?-wet:wet;
#else
    out[2*(i+j)+c]=v*65536;
#endif
   }hall_previous[c]=y;
  }
  hall_w=(hall_w+1)&(HRING-1);if(hall_fill<HRING)hall_fill++;
 }
}
