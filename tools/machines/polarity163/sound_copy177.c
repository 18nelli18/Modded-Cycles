/* Presse-papiers SoundCopy natif : extension RAM24 octets, jamais serialisee.
 * Les six constructeurs allouent128 au lieu de104 ; seul le bloc son100 est
 * copie nativement. L'extension contient un tag et les huit reglages LFO2.
 * Resolution de piste sans singleton/API UI : racine deja publiee et getters
 * virtuels natifs existants. Aucun fichier, allocation ou service audio. */
typedef unsigned int u32;typedef unsigned short u16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#define CLIP_TAG 0x4c463237u
extern volatile u32 lf2_context,lf2n_epoch,lf2n_seen,lp_one[6],lp_two[6];
static u32 lock(void){u32 sr;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");return sr;}
static void unlock(u32 sr){__asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");}
#ifdef LFO_COPY_COMMAND
#ifdef LFO_COPY_FOUR
volatile u32 lp_copy_api[5] __attribute__((section(".data")))={0};
static u32 extra_ready(void){return lp_copy_api[0]&&lp_copy_api[1]&&lp_copy_api[2]&&N(lp_copy_api[2])();}
#endif
static u32 source_track,destination_track,paste_ready;static u16 paste_values[8];
extern u32 lp_old_copy_command(u32),lp_old_paste_command(u32,u32,u32);
#ifdef LFO_CLEAR_COMMIT188
void lp_copy_source(u32 encoded){source_track=encoded;}
#endif
static u32 object_track(u32 object){u32 root=*(volatile u32*)0x40fe4228;if(root)for(u32 t=0;t<6;t++)if(N(0x40009c1a)(root+116,t)==object)return t;return 6;}
u32 lp_copy_command(u32 object){u32 t=object_track(object);source_track=t<6?t+1:0;u32 result=lp_old_copy_command(object);source_track=0;return result;}
u32 lp_paste_command(u32 object,u32 lane,u32 flags){u32 t=object_track(object);destination_track=t<6?t+1:0;source_track=destination_track;paste_ready=0;u32 result=lp_old_paste_command(object,lane,flags);
 if(result&&paste_ready&&t<6&&lf2_context){volatile u16*p=(volatile u16*)(lf2_context+192+t*16);u32 sr=lock();for(u32 i=0;i<8;i++)p[i]=paste_values[i];unlock(sr);}

#ifdef LFO_COPY_FOUR
 if(result&&paste_ready&&t<6&&lp_copy_api[4])N(lp_copy_api[4])(t);
#endif
 source_track=destination_track=paste_ready=0;return result;}
#endif
static u32 track(const u8 *raw){
 u32 root=*(volatile u32*)0x40fe4228;if(!root)return 6;
 for(u32 t=0;t<6;t++){
#ifdef LFO_TRACK_LOOKUP
  u32 obj=N(0x40009c1a)(root+116,t),vt=*(const u32*)obj;if(!vt)continue;
#else
  u32 obj=root+176+t*68,vt=*(const u32*)obj;if(!vt)continue;
#endif
  u32 getter=*(const u32*)(vt+40);if(getter&&N(getter)(obj)==(u32)raw)return t;
 }return 6;
}
static void base_settings(u16 *v,const u8 *raw){
 v[0]=*(const u16*)(raw+76);v[1]=*(const u16*)(raw+78);v[4]=*(const u16*)(raw+80);
 v[3]=*(const u16*)(raw+82);if(!v[3])v[3]=0x7f00;v[7]=*(const u16*)(raw+84);
}
static u32 valid(const u16 *v){return v[0]<32768&&(v[1]>>8)<24&&v[2]<32768&&((v[3]>>8)<33||(v[3]>>8)==127)&&(v[4]>>8)<7&&v[5]<32768&&(v[6]>>8)<5&&v[7]<32768;}
u32 lp_clip_capture(u8 *dst,const u8 *src,u32 bytes){
 u32 result=N(0x4008f1f0)(dst,src,bytes);if(bytes!=100)return result;
 u32 *tag=(u32*)(dst+100);u16 *v=(u16*)(dst+104);*tag=0;*(u32*)(dst+120)=0;
 if(src[38]==17)return result;
 v[2]=0x4000;v[5]=v[6]=0;
 u32 t=
#ifdef LFO_COPY_COMMAND
source_track?source_track-1:
#endif
track(src),ctx=lf2_context;
#ifdef LFO_COPY_LIVE
 u32 live=0;
 if(t<6&&ctx){
  const volatile u16 *p=(const volatile u16*)(ctx+192+t*16);u32 sr=lock();
  for(u32 i=0;i<8;i++)v[i]=p[i];unlock(sr);live=valid(v);
 }
 if(t<6&&(dst[79]&0xfc)!=0xa0)dst[79]=(u8)(0xa0|(lp_one[t]&1)|((lp_two[t]&1)<<1));
 if(live){
  /* Le menu lit ce contexte ; copier exactement ses valeurs visibles, meme
   * si le frame/son de base n'a pas encore recu la derniere publication. */
  *(u16*)(dst+76)=v[0];*(u16*)(dst+78)=(u16)((v[1]&0xff00)|dst[79]);
  *(u16*)(dst+80)=v[4];*(u16*)(dst+82)=v[3]==0x7f00?0:v[3];*(u16*)(dst+84)=v[7];
 }else{v[2]=0x4000;v[5]=v[6]=0;}
#else
 if(t<6&&ctx&&lf2n_epoch==lf2n_seen){
  const volatile u16 *p=(const volatile u16*)(ctx+192+t*16);u32 sr=lock();
  v[2]=p[2];v[5]=p[5];v[6]=p[6];unlock(sr);
 }
 if(t<6&&(dst[79]&0xfc)!=0xa0)dst[79]=(u8)(0xa0|(lp_one[t]&1)|((lp_two[t]&1)<<1));
#endif
 base_settings(v,dst);if(valid(v))*tag=CLIP_TAG;
#ifdef LFO_COPY_FOUR
 /* Buffer offsets124..155 belong to the enlarged160-byte native object. */
 for(u32 i=124;i<156;i++)dst[i]=0;
 if(t<6&&extra_ready()){
  const volatile u32*contexts=(const volatile u32*)lp_copy_api[0];const volatile u32*pol=(const volatile u32*)lp_copy_api[1];u32 flags=0,ok=1;
  for(u32 b=0;b<2;b++){
   if(!contexts[b]){ok=0;break;}const volatile u16*p=(const volatile u16*)(contexts[b]+192+t*16);u16*out=(u16*)(dst+124+b*16);u32 sr=lock();for(u32 i=0;i<8;i++)out[i]=p[i];unlock(sr);if(!valid(out))ok=0;flags|=(pol[b*6+t]&1)<<b;
  }
  if(ok)*(u32*)(dst+120)=0x4c340000u|flags;
 }
#endif
 return result;
}
u32 lp_clip_restore(u8 *dst,const u8 *src,u32 bytes){
 u32 result=N(0x4008f1f0)(dst,src,bytes);if(bytes!=100||dst[38]==17)return result;
 u32 t=
#ifdef LFO_COPY_COMMAND
destination_track?destination_track-1:
#endif
track(dst),ctx=lf2_context;
#ifdef LFO_COPY_FOUR
 if(t<6&&!ctx&&extra_ready())ctx=lf2_context;
#endif
 if(t>=6||!ctx)return result;
 u16 values[8];values[2]=0x4000;values[5]=values[6]=0;
 const u16 *saved=(const u16*)(src+104);
 if(*(const u32*)(src+100)==CLIP_TAG&&valid(saved)){values[2]=saved[2];values[5]=saved[5];values[6]=saved[6];}
 base_settings(values,dst);if(!valid(values))return result;
#ifdef LFO_COPY_COMMAND
 if(destination_track){for(u32 i=0;i<8;i++)paste_values[i]=values[i];paste_ready=1;}
#endif
 volatile u16 *p=(volatile u16*)(ctx+192+t*16);u32 sr=lock();for(u32 i=0;i<8;i++)p[i]=values[i];unlock(sr);
#ifdef LFO_COPY_FOUR
 if((*(const u32*)(src+120)&0xfffffffcu)==0x4c340000u&&valid((const u16*)(src+124))&&valid((const u16*)(src+140))&&extra_ready()){
  volatile u32*contexts=(volatile u32*)lp_copy_api[0];volatile u32*pol=(volatile u32*)lp_copy_api[1];u32 bits=*(const u32*)(src+120);sr=lock();
  for(u32 b=0;b<2;b++){volatile u16*q=(volatile u16*)(contexts[b]+192+t*16);const u16*v=(const u16*)(src+124+b*16);for(u32 i=0;i<8;i++)q[i]=v[i];for(u32 i=0;i<8;i++)((volatile u32*)(contexts[b]+t*32))[i]=0;pol[b*6+t]=(bits>>b)&1;}
  unlock(sr);if(lp_copy_api[3])N(lp_copy_api[3])();if(lp_copy_api[4])N(lp_copy_api[4])(t);
 }
#endif
 return result;
}
