/* Preference globale crusher ; sauvegarde UI seulement, transport arrete. */
typedef unsigned int u32;typedef unsigned char u8;
volatile u32 cr_mode;
volatile u32 cr_send[6];
#ifndef CR_LEAN_FX
static u32 send_loaded,send_dirty;
#endif
u32 cr_selected(void){u32 p=((u32(*)())0x400cf866)();if(!p)return 6;return ((u32(*)(u32))0x40012412)(p+48);}
#ifndef CR_LEAN_FX
static void cr_send_service(void){
 if(*(volatile u32*)0x40a7883c==1||!((u32(*)())0x400d0a10)())return;
 u8 b[18]={67,83,48,49},extra;u32 h[4]={0},ok=1;
 if(!send_loaded){send_loaded=1;
  if(!((u32(*)())0x4007bc5e)("/CrushSend.cfg","r",h)){
   ok=((u32(*)())0x4007baaa)(b,18,h)==18&&!((u32(*)())0x4007baaa)(&extra,1,h);
   if(((u32(*)())0x4007bc1c)(h))ok=0;
   ok=ok&&b[0]==67&&b[1]==83&&b[2]==48&&b[3]==49&&b[16]==165&&b[17]==90;
   for(u32 i=0;i<6;i++)if(b[4+i]>127||b[10+i]!=(u8)~b[4+i])ok=0;
   if(ok&&!send_dirty)for(u32 i=0;i<6;i++)cr_send[i]=b[4+i];
  }
 }
 if(send_dirty&&!((u32(*)())0x4007faf4)(2)){
  b[0]=67;b[1]=83;b[2]=48;b[3]=49;b[16]=165;b[17]=90;
  for(u32 i=0;i<6;i++){b[4+i]=cr_send[i];b[10+i]=~b[4+i];}
  h[0]=h[1]=h[2]=h[3]=0;
  if(!((u32(*)())0x4007bc5e)("/CrushSend.cfg","w",h)){
   ok=!((u32(*)())0x4007bb76)(h,0,18)&&((u32(*)())0x4007bb0a)(b,18,h)==18&&!((u32(*)())0x4007e2f6)(h);
   if(((u32(*)())0x4007bc1c)(h))ok=0;
   if(ok)send_dirty=0;
  }
 }
}

#endif
volatile u32 cr_rate=96,cr_bits=12;
static u32 loaded,dirty,last=0xffffffffu;static int mode_motion;
extern volatile u32 menu;
extern u32 cr_previous_draw(u32,u32);
extern void cr_notice(const char*),cr_show(u32);
#define N(a) ((u32(*)())(a))
static u32 packed(void){return cr_mode|(cr_rate<<8)|(cr_bits<<16);}
static u32 file(u32 write,u8 *buf){
 u32 h[4]={0,0,0,0},ok=0;u8 extra;
 if(N(0x4007bc5e)("/Crush.cfg",write?"w":"r",h))return 0;
 if(write){if(!N(0x4007bb76)(h,0,12)&&N(0x4007bb0a)(buf,12,h)==12&&!N(0x4007e2f6)(h))ok=1;}
 else if(N(0x4007baaa)(buf,12,h)==12&&!N(0x4007baaa)(&extra,1,h))ok=1;
 if(N(0x4007bc1c)(h))ok=0;return ok;
}
void cr_service(void){
 if(*(volatile u32*)0x40a7883c==1||!N(0x400d0a10)())return;
 u8 b[12]={67,82,48,50,0,96,12,255,159,243,165,90};
 if(!loaded){loaded=1;if(file(0,b)&&b[0]==67&&b[1]==82&&b[2]==48&&((b[3]==49&&b[4]<3)||(b[3]==50&&b[4]<5))&&b[5]<128&&b[6]>=2&&b[6]<=16&&b[7]==(u8)~b[4]&&b[8]==(u8)~b[5]&&b[9]==(u8)~b[6]&&b[10]==165&&b[11]==90){if(b[3]==49&&b[4]==2)b[4]=3;
#ifdef CR_LEAN_FX
if(b[4]>=3)b[4]=0;
#endif
last=b[4]|((u32)b[5]<<8)|((u32)b[6]<<16);if(!dirty){cr_mode=b[4];cr_rate=b[5];cr_bits=b[6];}}}
 if(dirty&&!N(0x4007faf4)(2)){u32 v=packed();if(v==last){dirty=0;return;}b[3]=50;b[4]=cr_mode;b[5]=cr_rate;b[6]=cr_bits;b[7]=~b[4];b[8]=~b[5];b[9]=~b[6];if(file(1,b)){last=v;dirty=0;}}
}
u32 cr_encoder(const u32 *e){
 if(!e||e[0]!=0x400fbebcu||menu||N(0x4007faf4)(13)||N(0x4007faf4)(8))return 0;
#ifndef CR_LEAN_FX
 if(e[3]==8){
  if((cr_mode!=3&&cr_mode!=4)||!N(0x4007faf4)(1)||N(0x4007faf4)(2))return 0;
  u32 lane=cr_selected();if(lane>=6)return 0;
  int delta=((int(*)(const u32*,u32,u32))0x4006f73a)(e,1,1);
  int v=(int)cr_send[lane]+delta;if(v<0)v=0;if(v>127)v=127;
  if((u32)v!=cr_send[lane]){cr_send[lane]=v;send_dirty=1;}
  cr_show(2);return 1;
 }
#endif
 if(e[3]!=15)return 0;
 u32 track=N(0x4007faf4)(2),func=N(0x4007faf4)(1);
 if(track&&func)return 0;
 int delta=((int(*)(const u32*,u32,u32))0x4006f73a)(e,1,1);
 if(track){if(delta){int sign=delta>0?1:-1;if(mode_motion*sign<0)mode_motion=0;mode_motion+=sign;if(mode_motion<2&&mode_motion>-2)return 1;mode_motion=0;u32 mode=cr_mode;
#ifdef CR_CENTER_DELAY
 /* Navigation seulement : les IDs CR02 et les routes DSP restent identiques. */
#ifdef CR_LEAN_FX
 static const u8 order[3]={2,1,0};u32 pos=2;
 for(u32 i=0;i<3;i++)if(order[i]==mode)pos=i;
 if(delta>0&&pos<2)pos++;
#else
 static const u8 order[5]={2,1,0,3,4};u32 pos=2;
 for(u32 i=0;i<5;i++)if(order[i]==mode)pos=i;
 if(delta>0&&pos<4)pos++;
#endif
 if(delta<0&&pos)pos--;mode=order[pos];
#else
 if(delta>0&&mode<4)mode++;if(delta<0&&mode)mode--;
#endif
 if(mode!=cr_mode){cr_mode=mode;dirty=1;}static const char *names[]={"Delay","Crush 1","Crush 2"
#ifndef CR_LEAN_FX
,"Both 1","Both 2"
#endif
};cr_notice(names[mode]);}return 1;}
 mode_motion=0;
 if(!cr_mode)return 0;
 int v=(int)(func?cr_bits:cr_rate)+delta,lo=func?2:0,hi=func?16:127;if(v<lo)v=lo;if(v>hi)v=hi;
 if((u32)v!=(func?cr_bits:cr_rate)){if(func)cr_bits=v;else cr_rate=v;dirty=1;}
 cr_show(!!func);return 1;
}
u32 cr_draw(u32 view,u32 canvas){if(!N(0x4007faf4)(2))mode_motion=0;
#ifndef CR_LEAN_FX
cr_send_service();
#endif
cr_service();return cr_previous_draw(view,canvas);}
