/* PS1 chaud : memes arrondis/etats que le noyau C historique. La voie froide
 * reste compilee separement pour conserver son cout de demarrage. Rings
 *2048echantillons avec stride2056, region privee46830000, sans CLOUD.
 */
#include "fx.h"
extern s16 ps_comb[2][4][2056],ps_ap[2][1024];
extern s32 ps_low[2][4],ps_filter[2][4],ps_previous[2];
extern u32 ps_w,ps_filled,ps_pos[2][2],ps_fill[2][2],ps_decay,ps_tone;
extern void fx_ps1_cold(s32*,const s32*,const s16*);
static u32 shared_input(const s32*in){
 for(u32 k=0;k<4;k++)if(ps_filter[0][k]!=ps_filter[1][k])return 0;
 for(u32 i=0;i<32;i++)if(((u32)in[2*i]^(u32)in[2*i+1])&0xffff0000u)return 0;
 return 1;
}
struct ps_job{s16*self,*other;const s32*input;s32*sum;u32 w,n,other_n;s32*low,*lowr;u32 tone,decay;};
extern void ps_comb_kernel(struct ps_job*);
extern void ps_input_kernel(s32*,const s32*,s32*);
struct ap_job{s32*out,*sum;s16*buf;u32 p0,p1,n0,n1;s32 previous;};
extern void ps_ap_kernel(struct ap_job*);
_Static_assert(sizeof(struct ps_job)==44,"ps_job ABI");
_Static_assert(sizeof(struct ap_job)==32,"ap_job ABI");
extern void ps_hot(s32*,const s32*,u32);
void ps_hot_core(s32*out,const s32*in,u32 shared){
 static const u32 length[4]={1187,1433,1709,1979},cross[4]={13,29,43,61};
 s32 io[64],*inputs=io,*sums=io+32;for(u32 i=0;i<32;i++)sums[i]=0;
 ps_input_kernel(inputs,in,ps_filter[0]);if(shared){for(u32 i=0;i<32;i+=2)inputs[i+1]=inputs[i];}else ps_input_kernel(inputs+1,in+1,ps_filter[1]);
 if(shared)for(u32 k=0;k<4;k++)ps_filter[1][k]=ps_filter[0][k];
 for(u32 k=0;k<4;k++){
  struct ps_job job={ps_comb[0][k],ps_comb[1][k],inputs,sums,ps_w,length[k],length[k]+cross[k],&ps_low[0][k],&ps_low[1][k],ps_tone<<16,ps_decay<<16};
  ps_comb_kernel(&job);
 }
 for(u32 c=0;c<2;c++){
  struct ap_job job={out+c,sums+c,ps_ap[c],ps_pos[c][0],ps_pos[c][1],277+31*c,397+47*c,ps_previous[c]};
  ps_ap_kernel(&job);ps_pos[c][0]=job.p0;ps_pos[c][1]=job.p1;ps_previous[c]=job.previous;
 }
 ps_w=(ps_w+16)&2047;
}
void fx_ps1(s32*out,const s32*in,const s16*params){
 if(ps_filled!=2048||(ps_w&15)){fx_ps1_cold(out,in,params);return;}
 u32 size=params[0]<0?0:(u32)params[0]>>8,tone=params[1]<0?0:(u32)params[1]>>8;
 if(size>127)size=127;if(tone>127)tone=127;
 u32 decay=16384+size*14900/127,damp=4096+tone*24576/127;
 ps_decay=(u32)((s32)ps_decay+(((s32)decay-(s32)ps_decay)>>5));ps_tone=(u32)((s32)ps_tone+(((s32)damp-(s32)ps_tone)>>5));
 ps_hot(out,in,shared_input(in));
}
