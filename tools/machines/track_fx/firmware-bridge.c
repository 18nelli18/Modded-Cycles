/* Relais audio : filtrer les seuls sends natifs rediriges vers un FX leger.
 * Le septieme input reverbe (retour delay) reste toujours dans le chemin stock.
 * Aucun fichier, allocation ou UI dans ces quatre appels du mixeur audio.
 */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
extern void mf_old_sum6(s32*,const s32*,s32*,const s32*),mf_old_sum7(s32*,const s32*,s32*,const s32*),mf_old_post(s32*),mf_sync_audio(void);
extern volatile u8 mf_live[48];
extern volatile u32 mf_mode,mf_audio_ready,mf_side,mf_side_on;
extern u32 lt_active,lt_run_slots(const s32*,const s32*,const u8*,const u32*,u32,s32*);
extern u32 lt_source_mask(u32);
static u32 sends[24],enabled;
static s32 left[192],right[192],wet[64];
static s32 clip(s32 x){return x>1048575?1048575:x< -1048576?-1048576:x;}
extern void lt_native_zero(s32*);
extern void lt_native_one(s32*,const s32*,s32*,const s32*);
static void native_sum(s32*out,const s32*in,s32*g,const s32*d,u32 count){
 u32 used=0,single=0;for(u32 t=0;t<count;t++)if(g[t]||d[t]){used++;single=t;}
 if(!used){lt_native_zero(out);return;}
 if(used==1){lt_native_one(out,in+32*single,g+single,d+single);return;}
 if(count==6)mf_old_sum6(out,in,g,d);else mf_old_sum7(out,in,g,d);
}
static void sum(s32*out,const s32*in,s32*g,const s32*d,u32 slot,u32 channel){
 u32 count=slot?6:7,redirect=0;for(u32 t=0;t<6;t++)redirect|=mf_live[slot*6+t];
 if(!redirect){native_sum(out,in,g,d,count);return;}
 s32 gain[7],delta[7];
 for(u32 t=0;t<count;t++){
  gain[t]=g[t];delta[t]=d[t];
  if(t<6){s32 target=(s32)((u32)g[t]+((u32)d[t]<<5));u32 amount=target<0?(0u-(u32)target)>>16:0;if(amount>32768)amount=32768;sends[slot*12+2*t+channel]=amount;
   if(mf_live[slot*6+t])gain[t]=delta[t]=0;
  }
 }
 native_sum(out,in,gain,delta,count);for(u32 t=0;t<count;t++)g[t]=(s32)((u32)g[t]+((u32)d[t]<<5));
}
void mf_sum6(s32*out,const s32*in,s32*g,const s32*d){
 if((u32)g==0x40a78bd0){mf_sync_audio();if(mf_mode&&mf_audio_ready){enabled=0;u32 kit=*(volatile u32*)0x40a78888,muted=*(volatile u8*)0x404e9b53;for(u32 t=0;t<6;t++)if(kit&&*(const u8*)(kit+28+100*t+38)!=17&&!(muted&(1u<<t)))enabled|=1u<<t;}}
 if(mf_mode&&mf_audio_ready&&((u32)g==0x40a78bd0||(u32)g==0x40a78bb8)){sum(out,in,g,d,1,(u32)g==0x40a78bb8);return;}
 native_sum(out,in,g,d,6);
}
void mf_sum7(s32*out,const s32*in,s32*g,const s32*d){
 if(mf_mode&&mf_audio_ready&&((u32)g==0x40a78b9c||(u32)g==0x40a78b80)){sum(out,in,g,d,0,(u32)g==0x40a78b80);return;}
 native_sum(out,in,g,d,7);
}
void mf_post(s32*mix){
 mf_old_post(mix);if(!mf_mode||!mf_audio_ready)return;
 u8 route[12];for(u32 t=0;t<6;t++){route[t]=mf_live[t];u32 d=mf_live[6+t];route[6+t]=d==1?6:d==2?7:d==3?5:0;}
 const s32*mid=(const s32*)0x80001858,*ls=mid,*rs=mid,*side=(const s32*)mf_side;const u32*on=(const u32*)mf_side_on;u32 stereo=0;
 u32 sources=0;
 if(side&&on)for(u32 t=0;t<6;t++)if((enabled&(1u<<t))&&(route[t]||route[6+t])){stereo|=on[t];sources|=1u<<t;}
 if(stereo){sources=lt_source_mask(sources);for(u32 t=0;t<6;t++)if(sources&(1u<<t))for(u32 i=0;i<32;i++){u32 j=32*t+i;s32 m=mid[j],s=on[t]?side[j]:0;left[j]=s?clip((m>>11)+(s>>11))*2048:m;right[j]=s?clip((m>>11)-(s>>11))*2048:m;}ls=left;rs=right;}
 if(lt_run_slots(ls,rs,route,sends,enabled,wet))for(u32 i=0;i<64;i++)mix[i]=clip((mix[i]>>11)+(wet[i]>>11))*2048;
}
