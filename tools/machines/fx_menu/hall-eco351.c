/* Eco HALL : deux combs partages, prises stereo et un diffuseur par cote.
 * Reseau3k, sortie48k raccordee. Apres1seconde sans entree : fondu21ms,
 * puis invalidation logique des rings, jamais d effacement massif en IRQ.
 * Compromis explicite : aussi pour INF dans cette comparaison privee.
 */
#include "fx.h"
extern s16 ps_comb[2][4][2056],ps_ap[2][1024];
extern u32 hall_w,hall_fill,hall_pos[2][2],hall_apfill[2][2],hall_decay,hall_tone;
extern s32 hall_low[2][4],hall_previous[2],hall_error[2][4];
extern volatile u32 eco_panic;
static u32 quiet,level,epoch;
#ifdef ECO_VOICE_FIRST
extern volatile u32 eco_irq_t0,eco_irq_active;
volatile u32 eco_calls,eco_shed,eco_max_entry,eco_seenIRQ;
static u32 hold,fade;
static s32 last[2],origin[2];
#endif
const char eco_hall_name[]="ECO HALL";
static s32 clamp16(s32 x){return x>32767?32767:x< -32768?-32768:x;}
static void empty(void){
 hall_w=hall_fill=0;
 for(u32 c=0;c<2;c++){
  hall_previous[c]=0;hall_pos[c][0]=hall_apfill[c][0]=0;
  for(u32 k=0;k<2;k++)hall_low[c][k]=hall_error[c][k]=0;
 }
}
void fx_hall(s32*out,const s32*in,const s16*params){
 if(epoch!=eco_panic){epoch=eco_panic;quiet=level=0;empty();
#ifdef ECO_VOICE_FIRST
 hold=fade=0;last[0]=last[1]=0;
 eco_calls=eco_shed=eco_max_entry=eco_seenIRQ=0;
#endif
 }
#ifdef ECO_VOICE_FIRST
 eco_calls++;u32 elapsed=0;
 if(eco_irq_active){eco_seenIRQ++;elapsed=*(volatile u32*)0xfc07000c-eco_irq_t0;if(elapsed>eco_max_entry)eco_max_entry=elapsed;}
 /* Budget local au wet : aucun seuil du gouverneur de voix n est change.
  * Le reseau est invalide avant reprise ; une ancienne queue ne peut surgir. */
 if(eco_irq_active&&elapsed>72000){
  if(!hold){origin[0]=last[0];origin[1]=last[1];fade=4;}
  hold=32;
 }
 if(hold){
  eco_shed++;
  hold--;if(hall_fill)empty();quiet=level=0;
  if(fade){
   fade--;s32 target[2]={origin[0]/4*(s32)fade,origin[1]/4*(s32)fade};
   s32 step[2]={(target[0]-last[0])/32,(target[1]-last[1])/32};
   for(u32 i=0;i<32;i++){last[0]+=step[0];last[1]+=step[1];out[2*i]=last[0];out[2*i+1]=last[1];}
   last[0]=target[0];last[1]=target[1];out[62]=last[0];out[63]=last[1];
  }else for(u32 i=0;i<64;i++)out[i]=0;
  return;
 }
#endif
 u32 energy=0;for(u32 i=0;i<64;i++)energy|=(u32)in[i];
 if(energy)quiet=0;else if(quiet<1532)quiet++;
 u32 previous_level=level;
 if(quiet>1500)level=level>=8?level-8:0;else if(energy||hall_fill)level=level<256?level+8:256;
 if(!level&&!energy&&!previous_level){
  if(hall_fill)empty();
  for(u32 i=0;i<64;i++)out[i]=0;
#ifdef ECO_VOICE_FIRST
  last[0]=last[1]=0;
#endif
  return;
 }
 u32 size=params[0]<0?0:(u32)params[0]>>8,tone=params[1]<0?0:(u32)params[1]>>8;
 if(size>127)size=127;if(tone>127)tone=127;
 u32 decay=size==127?32640:12288+size*19328/127;
 decay=(decay*decay)>>15;
 u32 residual=32768-(2048+tone*26624/127);residual=(residual*residual)>>15;
 u32 damp=32768-((residual*residual)>>15);
 if(!hall_fill){hall_decay=decay;hall_tone=damp;}
 else{hall_decay=(u32)((s32)hall_decay+(((s32)decay-(s32)hall_decay)>>5));hall_tone=(u32)((s32)hall_tone+(((s32)damp-(s32)hall_tone)>>5));}
 for(u32 i=0;i<32;i+=16){
  s32 input=0;
  for(u32 j=0;j<16;j++)input+=(in[2*(i+j)]>>21)+(in[2*(i+j)+1]>>21);
  s32 wet[2]={0,0};
  for(u32 k=0;k<2;k++){
   u32 n=k?207:165,other=n+(k?37:19);
   s32 old=hall_fill<n?0:ps_comb[0][k][(hall_w-n)&511];
   wet[0]+=old;wet[1]+=hall_fill<other?0:ps_comb[0][k][(hall_w-other)&511];
   s32 change=(old-hall_low[0][k])*(s32)hall_tone+hall_error[0][k];
   s32 low=hall_low[0][k]+(change>>15);hall_error[0][k]=change&32767;
   if(!input&&low>-2&&low<2)low=0;hall_low[0][k]=low;
   ps_comb[0][k][hall_w]=(s16)clamp16((input>>1)+(low*(s32)hall_decay)/32768);
  }
  for(u32 c=0;c<2;c++){
   s32 x=wet[c]/2;u32 p=hall_pos[c][0],n=c?42:38;
   s32 z=hall_apfill[c][0]<n?0:ps_ap[c][p];s32 y=clamp16(z-(x>>1));
   ps_ap[c][p]=(s16)clamp16(x+(y>>1));hall_pos[c][0]=p+1==n?0:p+1;
   if(hall_apfill[c][0]<n)hall_apfill[c][0]++;
   s32 previous=hall_previous[c];
   if(previous>=-8191&&previous<=8191&&y>=-8191&&y<=8191){
    s32 sample=previous*131072,step=(y-previous)*8192;
    for(u32 j=0;j<16;j++){sample+=step;out[2*(i+j)+c]=sample;}
   }else for(u32 j=0;j<16;j++){
    s32 v=previous+(y-previous)*(s32)(j+1)/16;u32 a=v<0?0u-(u32)v:(u32)v;
    s32 scaled=(s32)(a<8192?a*131072u:(24576u+a)*32768u);out[2*(i+j)+c]=v<0?-scaled:scaled;
   }
   hall_previous[c]=y;
  }
  hall_w=(hall_w+1)&511;if(hall_fill<512)hall_fill++;
 }
 if(level!=256||previous_level!=256){
  s32 phase=(s32)previous_level*32,delta=(s32)level-(s32)previous_level;
  for(u32 i=0;i<32;i++){phase+=delta;s32 gain=phase>>5;out[2*i]=(out[2*i]>>8)*gain;out[2*i+1]=(out[2*i+1]>>8)*gain;}
 }
#ifdef ECO_VOICE_FIRST
 last[0]=out[62];last[1]=out[63];
#endif
}
