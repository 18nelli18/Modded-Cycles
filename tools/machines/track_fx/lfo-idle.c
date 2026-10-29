/* Dispatcher secondaire : memes noyaux/etats natifs, copies32bits et voie OFF.
 * La banque2 avance meme OFF ;3/4 OFF restent figees comme dans le218.
 * Aucune modification du regulateur, de la qualite audio ou des fichiers. */
typedef unsigned int u32;typedef int s32;typedef unsigned short u16;
extern volatile u32 li_count,li_context,li_extra[2];
extern void li_sync_fast(u32,u32),li_update(u32,u32,u32,u32);
/* Groupes4mots : copie courte deroulee sans dupliquer tout le dispatcher. */
__attribute__((always_inline)) static inline void copy(u32*d,const u32*s,u32 n){
 while(n>=4){d[0]=s[0];d[1]=s[1];d[2]=s[2];d[3]=s[3];d+=4;s+=4;n-=4;}
 while(n--)*d++=*s++;
}
static u32 active(u32 ctx){if(!ctx)return 0;const u16*p=(const u16*)(ctx+192);for(u32 t=0;t<6;t++)if((p[t*8+3]>>8)<33)return 1;return 0;}
static void settings(u32 frame,u32 ctx){for(u32 t=0;t<6;t++)copy((u32*)(frame+16+t*66),(const u32*)(ctx+192+t*16),4);}
static void off_step(u32 frame,u32 ticks,u32 trigger,u32 ctx){
 u32 saved[24];for(u32 t=0;t<6;t++)copy(saved+t*4,(const u32*)(frame+16+t*66),4);
 settings(frame,ctx);li_update(frame,ticks,trigger,ctx);
 for(u32 t=0;t<6;t++)copy((u32*)(frame+16+t*66),saved+t*4,4);
}
static void mix(u32 out,u32 base,const u32*contexts,u32 n){
 copy((u32*)out,(const u32*)base,119);
 for(u32 t=0;t<6;t++){
  u32 index[4],used=0;s32 sum[4];
  for(u32 b=0;b<n;b++){
   if(!contexts[b])continue;const s32*p=(const s32*)(contexts[b]+t*32);u32 dest=(u32)p[4];if(dest>32)continue;
   u32 word=t*33+7+dest;if(word>=238)continue;u32 i=0;while(i<used&&index[i]!=word)i++;
   if(i==used){index[i]=word;sum[i]=((const u16*)base)[word];used++;}sum[i]+=p[5];
  }
  for(u32 i=0;i<used;i++){s32 v=sum[i];if(v<0)v=0;if(v>32512)v=32512;((u16*)out)[index[i]]=(u16)v;}
 }
}
void li_dispatch(u32 frame,u32 ticks,u32 trigger){
 u32 n=li_count;if(n<1||n>4)n=2;u32 ctx=li_context;
 if(n==1||!ctx){((void(*)(u32,u32,u32))0x40091ab2)(frame,ticks,trigger);return;}
 li_sync_fast(ctx,frame);
 u32 third=n>2&&li_extra[0]&&li_extra[1],on[2]={third?active(li_extra[0]):0,third&&n>3?active(li_extra[1]):0};
 if(!active(ctx)&&!on[0]&&!on[1]){
  ((void(*)(u32,u32,u32))0x40091ab2)(frame,ticks,trigger);off_step(frame,ticks,trigger,ctx);return;
 }
 u32 base=ctx+288;copy((u32*)base,(const u32*)frame,119);
 ((void(*)(u32,u32,u32))0x40091ab2)(frame,ticks,trigger);
 u32 work=ctx+764;copy((u32*)work,(const u32*)base,119);settings(work,ctx);li_update(work,ticks,trigger,ctx);
 u32 banks[4]={0x40fde838,ctx,0,0};
 if(on[0]||on[1])for(u32 b=0;b<2;b++){
  u32 extra=li_extra[b];if(!on[b]){for(u32 t=0;t<6;t++)((s32*)(extra+t*32))[4]=-1;continue;}
  work=extra+764;copy((u32*)work,(const u32*)base,119);settings(work,extra);li_update(work,ticks,trigger,extra);banks[b+2]=extra;
 }
 mix(frame,base,banks,4);
}
