/* ECO LEGACY: six-op core renders16 samples at24k, native envelopes stay48k/block.
 * The operator kernels double only their local frequency step; FmCore's native
 * phase advance remains32*freq. Output is held twice at the48k boundary. */
typedef unsigned int u32;typedef int s32;
extern void mf_old_eco_dx_block(u32,s32*);
void eco_dx_block(u32 lane,s32*out){
 mf_old_eco_dx_block(lane,out);
 for(int i=15;i>=0;i--){s32 x=out[i];out[2*i]=x;out[2*i+1]=x;}
}
