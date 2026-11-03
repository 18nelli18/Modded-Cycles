/* Coeur de routage : chemin commun compact, redistribution hors ligne.
 * Le noyau numerique et l'etat des sends restent les memes que362.
 * Aucun cache de pattern ; publication et synchronisation gardent leur ordre.
 */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
typedef u32 route_word __attribute__((may_alias));
extern volatile u8 mf_live[48];
extern volatile u32 mf_mode,mf_audio_ready;
extern u32 sends[24],enabled;
extern void mf_sync_audio(void),native_sum(s32*,const s32*,s32*,const s32*,u32);
static inline u32 redirected(u32 slot){
 const volatile route_word*p=(const volatile route_word*)mf_live;
 return slot?(p[1]&65535u)|p[2]:p[0]|(p[1]&0xffff0000u);
}
static __attribute__((always_inline)) inline void routed(s32*out,const s32*in,s32*g,const s32*d,u32 slot,u32 channel){
 u32 count=slot?6:7;
 s32 gain[7],delta[7];
 for(u32 t=0;t<count;t++){
  gain[t]=g[t];delta[t]=d[t];
  if(t<6){s32 target=(s32)((u32)g[t]+((u32)d[t]<<5));u32 amount=target<0?(0u-(u32)target)>>16:0;if(amount>32768)amount=32768;sends[slot*12+2*t+channel]=amount;
   if(mf_live[slot*6+t])gain[t]=delta[t]=0;
  }
 }
 native_sum(out,in,gain,delta,count);for(u32 t=0;t<count;t++)g[t]=(s32)((u32)g[t]+((u32)d[t]<<5));
}
static __attribute__((noinline)) void routed6(s32*out,const s32*in,s32*g,const s32*d,u32 channel){routed(out,in,g,d,1,channel);}
static __attribute__((noinline)) void routed7(s32*out,const s32*in,s32*g,const s32*d,u32 channel){routed(out,in,g,d,0,channel);}
void ac_sum6(s32*out,const s32*in,s32*g,const s32*d){
 if((u32)g==0x40a78bd0){mf_sync_audio();if(mf_mode&&mf_audio_ready){enabled=0;u32 kit=*(volatile u32*)0x40a78888,muted=*(volatile u8*)0x404e9b53;for(u32 t=0;t<6;t++)if(kit&&*(const u8*)(kit+28+100*t+38)!=17&&!(muted&(1u<<t)))enabled|=1u<<t;}}
 if(mf_mode&&mf_audio_ready&&((u32)g==0x40a78bd0||(u32)g==0x40a78bb8)&&redirected(1)){routed6(out,in,g,d,(u32)g==0x40a78bb8);return;}
 native_sum(out,in,g,d,6);
}
void ac_sum7(s32*out,const s32*in,s32*g,const s32*d){
 if(mf_mode&&mf_audio_ready&&((u32)g==0x40a78b9c||(u32)g==0x40a78b80)&&redirected(0)){routed7(out,in,g,d,(u32)g==0x40a78b80);return;}
 native_sum(out,in,g,d,7);
}
