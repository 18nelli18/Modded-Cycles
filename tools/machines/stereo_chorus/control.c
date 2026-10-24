/* Choix global Reverb/ChorusI/ChorusII ; E/S hors lecture et hors IRQ. */
typedef unsigned int u32;typedef unsigned char u8;
volatile u32 ch_mode;
static u32 loaded,dirty,last,labels=99;
static u32 saved_format[2];
u32 ch_format(u32 self,int value,char *out){
#ifdef CH_FORMAT_FIX
 /* Le service ne rafraichit pas les pointeurs pendant la lecture. Une ancienne
  * callback chorus doit deleguer sans attendre a Size/Tone natifs hors chorus. */
 u32 index=self==0x40a726a4?0:self==0x40a72708?1:2;
 if(ch_mode!=1&&ch_mode!=2&&index<2&&saved_format[index])
  return ((u32(*)(u32,int,char*))saved_format[index])(self,value,out);
#endif
 (void)self;value>>=8;if(value<0)value=0;if(value>127)value=127;return ((u32(*)(char*,const char*,...))0x40000e6e)(out,"%u",(u32)value);}
extern volatile u32 menu;
extern u32 ch_previous_draw(u32,u32);
extern void ch_notice(const char*);
#define N(a) ((u32(*)())(a))
#ifndef CH_SLOW_MODE_STEPS
static const char names[3][2][12]={{"Reverb Size","Reverb Tone"},{"Ch I Speed","Ch I Depth"},{"Ch II Speed","Ch II Depth"}};
#endif
void ch_labels(void){u32 m=ch_mode<3?ch_mode:0;if(labels==m)return;labels=m;
#ifndef CH_SLOW_MODE_STEPS
for(u32 i=0;i<12;i++){((volatile u8*)0x40129946)[i]=names[m][0][i];((volatile u8*)0x40129959)[i]=names[m][1][i];}
#endif
 for(u32 i=0;i<2;i++){volatile u32 *r=(volatile u32*)(0x40a71754+(39+i)*100);if(m){if(!saved_format[i]&&r[8]>=0x40000400&&r[8]<0x40100000)saved_format[i]=r[8];if(saved_format[i])r[8]=(u32)ch_format;}else if(saved_format[i])r[8]=saved_format[i];}
}
static u32 file(u32 write,u8 *buf){
 u32 h[4]={0,0,0,0},ok=0;u8 extra;
 if(N(0x4007bc5e)("/Chorus.cfg",write?"w":"r",h))return 0;
 if(write){if(!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(buf,8,h)==8&&!N(0x4007e2f6)(h))ok=1;}
 else if(N(0x4007baaa)(buf,8,h)==8&&!N(0x4007baaa)(&extra,1,h))ok=1;
 if(N(0x4007bc1c)(h))ok=0;return ok;
}
void ch_service(void){
 if(*(volatile u32*)0x40a7883c==1||!N(0x400d0a10)())return;
 u8 b[8]={67,72,48,49,0,255,165,90};
 if(!loaded){loaded=1;
  if(file(0,b)&&b[0]==67&&b[1]==72&&b[2]==48&&b[3]==49&&b[4]<3&&b[5]==(u8)~b[4]&&b[6]==165&&b[7]==90){if(!dirty)ch_mode=b[4];last=b[4];}
  else last=0;
 }
 if(dirty&&!N(0x4007faf4)(2)){u32 v=ch_mode;if(v==last){dirty=0;return;}b[4]=v;b[5]=~v;if(file(1,b)){last=v;dirty=0;}}
 ch_labels();
}
#ifdef CH_SLOW_MODE_STEPS
static int ch_mode_motion;
#endif
u32 ch_encoder(const u32 *e){
 if(!e||e[0]!=0x400fbebcu||e[3]!=14||menu||N(0x4007faf4)(13)||N(0x4007faf4)(8))return 0;
 ch_labels();if(!N(0x4007faf4)(2)||N(0x4007faf4)(1))return 0;
 int delta=((int(*)(const u32*,u32,u32))0x4006f73a)(e,1,1);
 #ifdef CH_SLOW_MODE_STEPS
 if(delta){int sign=delta>0?1:-1;if(ch_mode_motion*sign<0)ch_mode_motion=0;ch_mode_motion+=sign;if(ch_mode_motion<CH_SLOW_MODE_STEPS&&ch_mode_motion>-CH_SLOW_MODE_STEPS)return 1;ch_mode_motion=0;}
#endif
 if(delta){u32 mode=ch_mode;if(delta>0&&mode<2)mode++;if(delta<0&&mode)mode--;if(mode!=ch_mode){ch_mode=mode;dirty=1;}ch_labels();ch_notice(mode==2?"Chorus II":mode?"Chorus I":"Reverb");}
 return 1;
}
u32 ch_draw(u32 view,u32 canvas){
#ifdef CH_SLOW_MODE_STEPS
if(!N(0x4007faf4)(2))ch_mode_motion=0;
#endif
ch_service();return ch_previous_draw(view,canvas);}
