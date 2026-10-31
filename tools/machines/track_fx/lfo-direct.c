/* Native LFO state updates, one final mix. Secondary frames need only settings
 * because li_store_gate suppresses destination writes while collecting banks. */
typedef unsigned int u32;typedef int s32;typedef unsigned short u16;
extern volatile u32 li_count,li_context,li_extra[2];
extern void li_sync_fast(u32,u32),li_update(u32,u32,u32,u32);
volatile u32 li_noapply,li_active_tracks[3];
/* Bits0..5 : seules les destinations actives de chaque banque secondaire. */
static u32 active(u32 ctx){u32 mask=0;if(!ctx)return 0;const u16*p=(const u16*)(ctx+192);for(u32 t=0;t<6;t++)if((p[t*8+3]>>8)<33)mask|=1u<<t;return mask;}
static void settings(u32 frame,u32 ctx){for(u32 t=0;t<6;t++){u32*d=(u32*)(frame+16+t*66);const u32*s=(const u32*)(ctx+192+t*16);d[0]=s[0];d[1]=s[1];d[2]=s[2];d[3]=s[3];}}
static void mix(u32 frame,const u32*contexts){
 for(u32 t=0;t<6;t++){
  u32 index[4],used=0;s32 sum[4];
  for(u32 b=0;b<4;b++){
   if(!contexts[b]||(b&&!(li_active_tracks[b-1]&(1u<<t))))continue;const s32*p=(const s32*)(contexts[b]+t*32);u32 dest=(u32)p[4];if(dest>32)continue;
   u32 word=t*33+7+dest;if(word>=238)continue;u32 i=0;while(i<used&&index[i]!=word)i++;
   if(i==used){index[i]=word;sum[i]=((const u16*)frame)[word];used++;}sum[i]+=p[5];
  }
  for(u32 i=0;i<used;i++){s32 v=sum[i];if(v<0)v=0;if(v>32512)v=32512;((u16*)frame)[index[i]]=(u16)v;}
 }
}
void li_dispatch(u32 frame,u32 ticks,u32 trigger){
 u32 n=li_count;if(n<1||n>4)n=2;u32 ctx=li_context;
 if(n==1||!ctx){li_active_tracks[0]=li_active_tracks[1]=li_active_tracks[2]=0;((void(*)(u32,u32,u32))0x40091ab2)(frame,ticks,trigger);return;}
 li_sync_fast(ctx,frame);
 u32 third=n>2&&li_extra[0]&&li_extra[1],on[2]={third?active(li_extra[0]):0,third&&n>3?active(li_extra[1]):0};
 u32 second=active(ctx);li_active_tracks[0]=second;li_active_tracks[1]=on[0];li_active_tracks[2]=on[1];
 if(!second)for(u32 t=0;t<6;t++)((s32*)(ctx+t*32))[4]=-1;
 if(!second&&!on[0]&&!on[1]){
  ((void(*)(u32,u32,u32))0x40091ab2)(frame,ticks,trigger);
  return;
 }
 li_noapply=1;
 ((void(*)(u32,u32,u32))0x40091ab2)(frame,ticks,trigger);
 u32 work;
 if(second){work=ctx+764;settings(work,ctx);li_update(work,ticks,trigger,ctx);}
 u32 banks[4]={0x40fde838,second?ctx:0,0,0};
 if(on[0]||on[1])for(u32 b=0;b<2;b++){
  u32 extra=li_extra[b];if(!on[b]){for(u32 t=0;t<6;t++)((s32*)(extra+t*32))[4]=-1;continue;}
  work=extra+764;settings(work,extra);li_update(work,ticks,trigger,extra);banks[b+2]=extra;
 }
 li_noapply=0;mix(frame,banks);
}
