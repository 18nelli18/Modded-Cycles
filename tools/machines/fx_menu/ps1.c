#include "fx.h"
#ifdef FX_PS1
/* Reverb originale inspiree SPU : precision16bits, quatre combs avec
 * reflexions croisees et amortissement IIR, deux allpass stereo. Traitement
 * demi-debit24kHz adapte au bus48kHz des Cycles : pas une emulation exacte.
 * Aucune donnee de jeu/Sony, aucun malloc ; tailles et coefficients originaux.
 */
/* Huit lignes courantes distantes de4096o entraient en conflit dans le cache
 * quatre voies (index modulo2048). Espace16o : huit sets distincts, meme
 * ring2048/masque et memes PCM. Le padding ne fait jamais partie du signal. */
#ifdef FX_PS1_CACHE_OPT
#define PS_COMB_STRIDE 2056
#else
#define PS_COMB_STRIDE 2048
#endif
static s16 ps_comb[2][4][PS_COMB_STRIDE],ps_ap[2][1024];
static s32 ps_low[2][4],ps_filter[2][4],ps_previous[2];
static u32 ps_w,ps_filled,ps_pos[2][2],ps_fill[2][2],ps_decay,ps_tone;
static s32 sat16(s32 x){return x>32767?32767:x< -32768?-32768:x;}
void fx_ps1_reset(void){
 ps_w=ps_filled=ps_decay=ps_tone=0;
 for(u32 c=0;c<2;c++){
  ps_previous[c]=0;
  for(u32 k=0;k<4;k++)ps_low[c][k]=ps_filter[c][k]=0;
  for(u32 k=0;k<2;k++)ps_pos[c][k]=ps_fill[c][k]=0;
 }
}
static s32 diffuse(s32 x,u32 c){
 for(u32 k=0;k<2;k++){
  u32 length=k?397+47*c:277+31*c,pos=ps_pos[c][k],at=k*512+pos;
  s32 z=ps_fill[c][k]<length?0:ps_ap[c][at];
  if(x>-2&&x<2&&z>-2&&z<2)x=z=0;
  s32 y=sat16(z-(x>>1));ps_ap[c][at]=(s16)sat16(x+(y>>1));x=y;
  if(ps_fill[c][k]<length)ps_fill[c][k]++;
  ps_pos[c][k]=pos+1==length?0:pos+1;
 }
 return x;
}
#ifdef FX_VOICE_OPT
/* Seuls les quatre filtres d entree sont partageables. La reverb stereo
 * (reflexions/comb/allpass) garde ses deux etats et ses deux sorties. */
__attribute__((always_inline)) static inline s32 input_pair(const s32*in,u32 i,u32 c){
 s32 sum=0;
 for(u32 j=0;j<2;j++){
  s32 x=in[2*(i+j)+c]>>16;
  for(u32 k=0;k<4;k++){s32 z=x+ps_filter[c][k];ps_filter[c][k]=x;x=z/2;}
  sum+=x;
 }
 return sum;
}
static u32 shared_input(const s32*in){
 for(u32 k=0;k<4;k++)if(ps_filter[0][k]!=ps_filter[1][k])return 0;
 for(u32 i=0;i<32;i++)if(((u32)in[2*i]^(u32)in[2*i+1])&0xffff0000u)return 0;
 return 1;
}
#endif
#ifdef FX_VOICE_OPT
/* Eviter de dupliquer toute la reverb pour le seul test mono/stereo. */
__attribute__((optimize("no-unswitch-loops")))
#endif
void fx_ps1(s32*out,const s32*in,const s16*params){
 static const u32 length[4]={1187,1433,1709,1979},cross[4]={13,29,43,61};
 u32 size=params[0]<0?0:(u32)params[0]>>8,tone=params[1]<0?0:(u32)params[1]>>8;
 if(size>127)size=127;if(tone>127)tone=127;
 u32 decay=16384+size*14900/127,damp=4096+tone*24576/127;
 if(!ps_filled){ps_decay=decay;ps_tone=damp;}
 else{ps_decay=(u32)((s32)ps_decay+(((s32)decay-(s32)ps_decay)>>5));ps_tone=(u32)((s32)ps_tone+(((s32)damp-(s32)ps_tone)>>5));}
#ifdef FX_VOICE_OPT
 u32 shared=shared_input(in);
#endif
 for(u32 i=0;i<32;i+=2){
  s32 input[2]={0,0},sum[2]={0,0};
#ifdef FX_VOICE_OPT
  input[0]=input_pair(in,i,0);input[1]=shared?input[0]:input_pair(in,i,1);
#else
  for(u32 j=0;j<2;j++)for(u32 c=0;c<2;c++){
   s32 x=in[2*(i+j)+c]>>16;
   for(u32 k=0;k<4;k++){s32 z=x+ps_filter[c][k];ps_filter[c][k]=x;x=z/2;}
   input[c]+=x;
  }
#endif
  if(ps_filled<2048)ps_filled++;
  for(u32 k=0;k<4;k++){
   s32 old[2];
   for(u32 c=0;c<2;c++){u32 n=length[k]+c*cross[k];old[c]=ps_filled<=n?0:ps_comb[c][k][(ps_w-n)&2047];sum[c]+=old[c];}
   for(u32 c=0;c<2;c++){
    s32 reflected=(7*old[c]+old[1-c])/8,low=ps_low[c][k];
    low+=((reflected-low)*(s32)ps_tone)>>15;
    if(!input[c]&&low>-2&&low<2)low=0;
    ps_low[c][k]=low;ps_comb[c][k][ps_w]=(s16)sat16((input[c]>>2)+((low*(s32)ps_decay)>>15));
   }
  }
  for(u32 c=0;c<2;c++){
   s32 y=diffuse(sum[c]/4,c),previous=ps_previous[c];
   out[2*i+c]=((previous+y)/2)*65536;out[2*(i+1)+c]=y*65536;ps_previous[c]=y;
  }
  ps_w=(ps_w+1)&2047;
 }
#ifdef FX_VOICE_OPT
 if(shared)for(u32 k=0;k<4;k++)ps_filter[1][k]=ps_filter[0][k];
#endif
}
#endif
