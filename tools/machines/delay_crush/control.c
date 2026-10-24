/* Preference globale crusher ; sauvegarde UI seulement, transport arrete. */
typedef unsigned int u32;typedef unsigned char u8;
volatile u32 cr_mode;
volatile u32 cr_rate=96,cr_bits=12;
static u32 loaded,dirty,last=0xffffffffu;
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
 u8 b[12]={67,82,48,49,0,96,12,255,159,243,165,90};
 if(!loaded){loaded=1;if(file(0,b)&&b[0]==67&&b[1]==82&&b[2]==48&&b[3]==49&&b[4]<3&&b[5]<128&&b[6]>=2&&b[6]<=16&&b[7]==(u8)~b[4]&&b[8]==(u8)~b[5]&&b[9]==(u8)~b[6]&&b[10]==165&&b[11]==90){last=b[4]|((u32)b[5]<<8)|((u32)b[6]<<16);if(!dirty){cr_mode=b[4];cr_rate=b[5];cr_bits=b[6];}}}
 if(dirty&&!N(0x4007faf4)(2)){u32 v=packed();if(v==last){dirty=0;return;}b[4]=cr_mode;b[5]=cr_rate;b[6]=cr_bits;b[7]=~b[4];b[8]=~b[5];b[9]=~b[6];if(file(1,b)){last=v;dirty=0;}}
}
u32 cr_encoder(const u32 *e){
 if(!e||e[0]!=0x400fbebcu||e[3]!=15||menu||N(0x4007faf4)(13)||N(0x4007faf4)(8))return 0;
 u32 track=N(0x4007faf4)(2),func=N(0x4007faf4)(1);
 if(track&&func)return 0;
 int delta=((int(*)(const u32*,u32,u32))0x4006f73a)(e,1,1);
 if(track){u32 mode=cr_mode;if(delta>0&&mode<2)mode++;if(delta<0&&mode)mode--;if(mode!=cr_mode){cr_mode=mode;dirty=1;}cr_notice(mode==2?"Delay + Crush":mode?"Crush":"Delay");return 1;}
 if(!cr_mode)return 0;
 int v=(int)(func?cr_bits:cr_rate)+delta,lo=func?2:0,hi=func?16:127;if(v<lo)v=lo;if(v>hi)v=hi;
 if((u32)v!=(func?cr_bits:cr_rate)){if(func)cr_bits=v;else cr_rate=v;dirty=1;}
 cr_show(!!func);return 1;
}
u32 cr_draw(u32 view,u32 canvas){cr_service();return cr_previous_draw(view,canvas);}
