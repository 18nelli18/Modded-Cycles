/* Meme postmix et memes buffers ; aucune preparation sans route ni queue.
 * mf_requested est publie avec mf_live par slot-state.c sous verrou IRQ.
 * lt_active est possede par le DSP et conserve les queues independamment.
 */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
extern volatile u32 mf_mode,mf_audio_ready,mf_requested,mf_side,mf_side_on;
extern volatile u8 mf_live[48];
extern u32 lt_active,enabled,sends[24],lt_source_mask(u32);
extern s32 left[192],right[192],wet[64];
extern void mf_old_post(s32*);
extern u32 lt_run_slots(const s32*,const s32*,const u8*,const u32*,u32,s32*);
static __attribute__((always_inline)) inline s32 clip(s32 x){return x>1048575?1048575:x< -1048576?-1048576:x;}
void ac_post(s32*mix){
 mf_old_post(mix);
 if(!mf_mode||!mf_audio_ready||(!mf_requested&&!lt_active))return;
 u8 route[12];for(u32 t=0;t<6;t++){route[t]=mf_live[t];u32 d=mf_live[6+t];route[6+t]=d==1?6:d==2?7:d==3?5:0;}
 const s32*mid=(const s32*)0x80001858,*ls=mid,*rs=mid,*side=(const s32*)mf_side;const u32*on=(const u32*)mf_side_on;u32 stereo=0;
 u32 sources=0;
 if(side&&on)for(u32 t=0;t<6;t++)if((enabled&(1u<<t))&&(route[t]||route[6+t])){stereo|=on[t];sources|=1u<<t;}
 if(stereo){sources=lt_source_mask(sources);for(u32 t=0;t<6;t++)if(sources&(1u<<t))for(u32 i=0;i<32;i++){u32 j=32*t+i;s32 m=mid[j],s=on[t]?side[j]:0;left[j]=s?clip((m>>11)+(s>>11))*2048:m;right[j]=s?clip((m>>11)-(s>>11))*2048:m;}ls=left;rs=right;}
 if(lt_run_slots(ls,rs,route,sends,enabled,wet))for(u32 i=0;i<64;i++)mix[i]=clip((mix[i]>>11)+(wet[i]>>11))*2048;
}
