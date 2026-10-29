typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
/* Gain exactement1 au debut, exactement0 a la fin, precision32bits.
 * Ne change que les blocs deja choisis pour extinction par le regulateur. */
void gv_fade(u32 lane,s32*buffer){
 volatile u8*fading=(volatile u8*)0x46732058,*length=(volatile u8*)0x46732052,*stolen=(volatile u8*)0x4673204c;
 u32 remain=fading[lane],len=length[lane];if(!remain||!len||remain>len)return;
 u32 n=len*32,position=(len-remain)*32,step=65536/(n-1),gain=65536-position*step;
 for(u32 i=0;i<32;i++,gain-=step){u32 g=position+i==n-1?0:gain;s32 x=buffer[i];buffer[i]=(x>>16)*(s32)g+(s32)((((u32)x&65535)*g)>>16);}
 fading[lane]=remain-1;if(remain==1)stolen[lane]=1;
}
