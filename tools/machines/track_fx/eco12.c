/* LEGACY only: 8 internal samples per 32-sample/48k block, held four times.
 * Envelopes/LFO and native core phase advance retain their original timing. */
typedef unsigned int u32;typedef int s32;
extern void mf_old_eco_dx_block(u32,s32*);
void eco_dx_block(u32 lane,s32*out){
 mf_old_eco_dx_block(lane,out);
 for(int i=7;i>=0;i--){s32 x=out[i];out[4*i]=x;out[4*i+1]=x;out[4*i+2]=x;out[4*i+3]=x;}
}
