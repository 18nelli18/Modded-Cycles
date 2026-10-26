/* Quatre LFO audio : UI partagee, trois contextes secondaires independants.
 * Aucun pointeur UI temporaire n'est lu par le dispatch audio. */
typedef unsigned int u32;typedef int s32;typedef unsigned short u16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 lf2_context,lf2p_row,lf2p_edit,lf2p_track,lf2p_assigned;
extern volatile u32 lp_one[6],lp_two[6],lp_dirty;
extern u32 mx_old_prepare(u32),lf2_launch(u32),mx_old_key(u32,const u32*),mx_old_pol_encoder(u32,const u32*);
extern void mx_old_write(u32,u32,u32),lf2_init(u32,u32),lf2_update(u32,u32,u32,u32),mx_old_dispatch(u32,u32,u32);
extern void mx_old_render(u32,u32),mx_old_frame(void),mx_old_change(u32);
extern u32 fxp_crc(const u8*,u32);
volatile u32 mx_ui_context,mx_selected,mx_extra[2],mx_polarity[12];
#ifdef MX_LAZY_START
volatile u32 mx_armed;
#endif
#ifdef MX_COUNT_OPTION
volatile u32 mx_count __attribute__((section(".bss.mxcount")));
static u32 count_loaded,count_dirty;
static void capture(void);
void mx_select(u32);
u32 mx_count_get(void){u32 n=mx_count;return n>=1&&n<=4?n:2;}
void mx_count_set(u32 n){if(n<1||n>4||n==mx_count_get())return;capture();mx_count=n;count_dirty=1;if(mx_selected+2>n)mx_select(0);}
#else
u32 mx_count_get(void){return 4;}
#endif
#ifdef MX_COMPACT_RAM
static u8 *mx_storage;
#endif
static u32 contexts[2][310];
static const struct {u32 len,cap,refs;char text[8];} titles[3]={{5,5,~0u,"LFO 2"},{5,5,~0u,"LFO 3"},{5,5,~0u,"LFO 4"}};
static void copy(u8*d,const u8*s,u32 n){while(n--)*d++=*s++;}
static void zero(u8*d,u32 n){while(n--)*d++=0;}
static u32 lock(void){u32 sr;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");return sr;}
static void unlock(u32 sr){__asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");}
u32 mx_prepare(u32 frame){
 u32 result=mx_old_prepare(frame);if(!result)return 0;
#ifdef MX_COMPACT_RAM
 if(mx_count_get()>2&&!mx_storage){mx_storage=(u8*)N(0x400802e0)(16+96*192+48+96*192);if(!mx_storage)return 0;}
#endif
 if(mx_count_get()>2&&!mx_extra[0]){for(u32 b=0;b<2;b++)lf2_init((u32)contexts[b],frame);mx_extra[1]=(u32)contexts[1];mx_extra[0]=(u32)contexts[0];}
 if(!mx_selected)mx_ui_context=lf2_context;
 return result;
}
void mx_select(u32 bank){
 if(bank>2)bank=0;mx_selected=bank;mx_ui_context=bank?mx_extra[bank-1]:lf2_context;lf2p_edit=0;
}
u32 mx_launch(u32 view){if(mx_count_get()<2)return 0;mx_select(0);u32 result=lf2_launch(view);
#ifdef MX_LAZY_START
 if(result)mx_armed=1;
#endif
 return result;}
u32 mx_key(u32 view,const u32*e){
 if(e&&e[3]==8&&!(e[4]&3)&&!lf2p_assigned&&mx_selected+2<mx_count_get()){mx_select(mx_selected+1);N(0x40076082)(view);return 1;}
 u32 close=e&&((e[3]==8&&!(e[4]&3)&&!lf2p_assigned)||((e[3]==12||e[3]==13)&&(e[4]&9)==1));
 u32 result=mx_old_key(view,e);if(close)mx_select(0);return result;
}
void mx_render(u32 view,u32 canvas){*(u32*)(view+0x500+148)=(u32)titles[mx_selected<3?mx_selected:0].text;mx_old_render(view,canvas);}
void mx_write(u32 track,u32 field,u32 value){if(!mx_selected)mx_old_write(track,field,value);}
u32 mx_pol_encoder(u32 view,const u32*e){
 if(mx_selected&&e&&e[0]==0x400fbebc&&e[3]==1&&lf2p_row==9){
  s32 delta=(s32)N(0x4006f73a)(e,1,1);
  if(lf2p_edit){if(delta&&lf2p_track<6)mx_polarity[(mx_selected-1)*6+lf2p_track]=delta>0;}
  else if(delta<0)lf2p_row=0;N(0x40076082)(view);return 1;
 }return mx_old_pol_encoder(view,e);
}
void mx_pol_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){
 (void)a;(void)b;(void)x;u32 t=lf2p_track<6?lf2p_track:0;
 u32 uni=mx_selected?mx_polarity[(mx_selected-1)*6+t]:lp_two[t];
 N(0x40071a04)(canvas,0x40ea14cc,120,y,4,"%s",uni?"Uni":"Bi");
}
static u32 active(u32 ctx){if(!ctx)return 0;const u16*p=(const u16*)(ctx+192);for(u32 t=0;t<6;t++)if(p[t*8+3]>>8<33)return 1;return 0;}
/* Contribution native par banque, puis une seule saturation apres sommation. */
void mx_mix(u32 out,u32 base){
 copy((u8*)out,(const u8*)base,476);
 for(u32 t=0;t<6;t++){
  u32 index[4],count=0;s32 sum[4];
  for(u32 b=0;b<mx_count_get();b++){
   u32 ctx=b==0?0x40fde838:b==1?lf2_context:mx_extra[b-2];if(!ctx)continue;
   const s32*state=(const s32*)(ctx+t*32);u32 dest=(u32)state[4];if(dest>32)continue;
   u32 word=t*33+7+dest;if(word>=238)continue;u32 i=0;while(i<count&&index[i]!=word)i++;
   if(i==count){index[count]=word;sum[count]=((const u16*)base)[word];count++;}sum[i]+=state[5];
  }
  for(u32 i=0;i<count;i++){s32 v=sum[i];if(v<0)v=0;if(v>32512)v=32512;((u16*)out)[index[i]]=(u16)v;}
 }
}
void mx_dispatch(u32 frame,u32 ticks,u32 trigger){
 u32 count=mx_count_get();if(count==1){N(0x40091ab2)(frame,ticks,trigger);return;}
 mx_old_dispatch(frame,ticks,trigger);if(count==2||!lf2_context||!mx_extra[0])return;
 u32 enabled[2]={active(mx_extra[0]),count>3?active(mx_extra[1]):0};if(!enabled[0]&&!enabled[1])return;
 u32 base=lf2_context+288;
 for(u32 b=0;b<2;b++){
  u32 ctx=mx_extra[b];if(!enabled[b]){for(u32 t=0;t<6;t++)((s32*)(ctx+t*32))[4]=-1;continue;}
  u8*work=(u8*)(ctx+764);copy(work,(const u8*)base,476);
  for(u32 t=0;t<6;t++)copy(work+16+t*66,(const u8*)(ctx+192+t*16),16);
  lf2_update((u32)work,ticks,trigger,ctx);
 }
 mx_mix(frame,base);
}
/* Banque de travail 96 patterns, index natif ; E/S seulement dans la tache UI. */
#define ROW 192
#define PAYLOAD (96*ROW+48)
#ifdef MX_COMPACT_RAM
#define patterns ((u8 (*)[ROW])mx_storage)
#define packet (mx_storage+96*ROW)
#else
static u8 patterns[96][ROW],packet[16+PAYLOAD];
#endif
#define PACKET_SIZE (16+PAYLOAD)
static u32 ready,project,current=96,dirty,saved_crc,last_pol[12];
static char path[24];
static void defaults(u8*row){for(u32 b=0;b<2;b++)for(u32 t=0;t<6;t++){u16*p=(u16*)(row+b*96+t*16);p[0]=0x7000;p[1]=0x400;p[2]=0x4000;p[3]=0x7f00;p[4]=p[5]=p[6]=0;p[7]=0x4000;}}
static void capture(void){
 if(!ready||current>95||!mx_extra[0])return;
 for(u32 b=0;b<2;b++){const u8*src=(const u8*)(mx_extra[b]+192);u8*dst=patterns[current]+b*96;for(u32 i=0;i<96;i++)if(dst[i]!=src[i]){dst[i]=src[i];dirty=1;}}
}
static void restore(u32 id){
 if(id>95||!mx_extra[0])return;u32 sr=lock();
 for(u32 b=0;b<2;b++){zero((u8*)mx_extra[b],192);copy((u8*)(mx_extra[b]+192),patterns[id]+b*96,96);}current=id;unlock(sr);
}
void mx_pattern(u32 ptr){
 if(!ready||!ptr||!mx_extra[0])return;u32 id=*(const u32*)(ptr+30706);if(id>95||id==current)return;
 u32 sr=lock();capture();restore(id);unlock(sr);
}
void mx_change(u32 ptr){mx_old_change(ptr);mx_pattern(ptr);}
static u32 valid(const u8*p){
 for(u32 row=0;row<96;row++)for(u32 t=0;t<12;t++){
  const u16*v=(const u16*)(p+row*ROW+t*16);
  if(v[0]>32767||v[1]>>8>23||v[2]>32767||(v[3]>>8>32&&v[3]>>8!=127)||v[4]>>8>6||v[5]>32767||v[6]>>8>4||v[7]>32767)return 0;
 }for(u32 i=0;i<12;i++)if(((const u32*)(p+96*ROW))[i]>1)return 0;return 1;
}
static void pathname(u32 id){const char hex[]="0123456789abcdef";const char pre[]="/L34_";for(u32 i=0;i<5;i++)path[i]=pre[i];for(u32 i=0;i<8;i++)path[5+i]=hex[(id>>(28-4*i))&15];path[13]='.';path[14]='c';path[15]='f';path[16]='g';path[17]=0;}
static void load(u32 id){
 ready=0;u32 h[4]={0};u8 extra;for(u32 i=0;i<96;i++)defaults(patterns[i]);zero((u8*)mx_polarity,48);pathname(id);saved_crc=0;
 if(!N(0x4007bc5e)(path,"r",h)){
  u32 ok=N(0x4007baaa)(packet,PACKET_SIZE,h)==PACKET_SIZE&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);
  const u32*head=(const u32*)packet;
  if(ok&&head[0]==0x4c333432&&head[1]==id&&head[2]==PAYLOAD&&head[3]==fxp_crc(packet+16,PAYLOAD)&&valid(packet+16)){
   copy((u8*)patterns,packet+16,96*ROW);copy((u8*)mx_polarity,packet+16+96*ROW,48);saved_crc=head[3];
  }
 }project=id;ready=1;dirty=0;current=96;for(u32 i=0;i<12;i++)last_pol[i]=mx_polarity[i];
}
static void service(void){
 if(!mx_extra[0])return;u32 kit=N(0x400cf866)();if(!kit)return;u32 id=N(0x4000eae2)(kit);if(!id)return;
 if(!ready||project!=id)load(id);
 mx_pattern(*(volatile u32*)0x40a7887c);capture();
 for(u32 i=0;i<12;i++)if(last_pol[i]!=mx_polarity[i]){last_pol[i]=mx_polarity[i];dirty=1;}
 if(*(volatile u32*)0x40a78874||*(volatile u32*)0x40a7883c)return;
 if(!dirty&&saved_crc)return;
 copy(packet+16,(const u8*)patterns,96*ROW);copy(packet+16+96*ROW,(const u8*)mx_polarity,48);
 u32 crc=fxp_crc(packet+16,PAYLOAD);if(!dirty&&crc==saved_crc)return;
 u32*head=(u32*)packet;head[0]=0x4c333432;head[1]=project;head[2]=PAYLOAD;head[3]=crc;u32 h[4]={0};
 if(!N(0x4007bc5e)(path,"w",h)){u32 ok=!N(0x4007bb76)(h,0,PACKET_SIZE)&&N(0x4007bb0a)(packet,PACKET_SIZE,h)==PACKET_SIZE&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok){dirty=0;saved_crc=crc;}}
}
#ifdef MX_COUNT_OPTION
static void count_service(void){
 u32 h[4]={0};u8 b[8],extra;
 if(!count_loaded){count_loaded=1;if(!count_dirty&&!N(0x4007bc5e)("/LfoCount.cfg","r",h)){
  u32 ok=N(0x4007baaa)(b,8,h)==8&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);
  if(ok&&b[0]=='L'&&b[1]=='C'&&b[2]==1&&b[3]>=1&&b[3]<=4&&b[4]==(u8)~b[3]&&b[5]==165&&b[6]==90&&b[7]==0)mx_count=b[3];
 }}
 if(!count_dirty||*(volatile u32*)0x40a78874||*(volatile u32*)0x40a7883c)return;
 b[0]='L';b[1]='C';b[2]=1;b[3]=mx_count_get();b[4]=~b[3];b[5]=165;b[6]=90;b[7]=0;
 if(!N(0x4007bc5e)("/LfoCount.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(b,8,h)==8&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)count_dirty=0;}
}
#endif
void mx_frame(void){mx_old_frame();
#ifdef MX_COUNT_OPTION
 u32 level;__asm__ volatile("move.w %%sr,%0":"=d"(level));
 if((level&0x700)||!*(volatile u32*)0x40fe4178||*(volatile u32*)0x40a7883c||!N(0x400d0a10)())return;
 count_service();if(mx_count_get()>2)mx_prepare(0x8000100c);service();return;
#endif
#ifdef MX_LAZY_START
 if(!mx_armed)return;
 u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if((sr&0x700)||*(volatile u32*)0x40a7883c==1||!N(0x400d0a10)())return;
#else
 if(*(volatile u32*)0x40fe4178)mx_prepare(0x8000100c);
#endif
 service();}
