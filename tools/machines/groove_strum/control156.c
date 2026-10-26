/* Groove/Strum : adaptation UI originale ; noyaux et tables PPPCCC MIT.
 * Les gestes et fichiers des autres mods restent leurs proprietaires.
 * Aucun appel UI/fichier dans le sequencer ni le render CHORD. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;typedef signed char s8;
#define N(a) ((u32(*)())(a))
extern volatile u32 menu,row,sx_submenu,du_page,mq_page;
extern u32 wf_menu_edit(void),gc_previous_key(const u32*),gc_previous_encoder(const u32*),gc_previous_draw(u32,u32);
extern void gc_previous_frame(void),gc_sub_draw(u32,u32);
volatile u8 gc_amounts[12];volatile u8 gc_groove;volatile s8 gc_strum;volatile u32 gc_ticks[6],gc_g0;
u32 gc_rng=0x01234567;
volatile u32 gc_page,gc_row,gc_edit,gc_track;
static u32 dirty,loaded,owned_back,owned_data;
static const char*names[8]={"Swng","BBap","Disc","Regg","Bong","Caix","High","Kudu"};
static u32 playing(void){return (*(volatile u32*)0x40a78874|*(volatile u32*)0x40a7883c)==1;}
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
static volatile u8*header(void){return gc_amounts;}
static s32 clamp(s32 x,s32 lo,s32 hi){return x<lo?lo:x>hi?hi:x;}
static u32 amount(u32 velocity){volatile u8*p=header();u32 v=p?p[6*velocity+(gc_track<6?gc_track:0)]:0;return v<=100?v:0;}
void gc_adjust(s32 delta){
 if(!delta)return;
 if(gc_row==0){gc_groove=(u8)clamp((s32)gc_groove+delta,0,7);dirty=1;}
 else if(gc_row==1)gc_track=(u32)clamp((s32)gc_track+delta,0,6);
 else if(gc_row==4){gc_strum=(s8)clamp((s32)gc_strum+delta,-80,80);dirty=1;}
 else if(gc_row==2||gc_row==3){volatile u8*p=header();if(p){u32 off=(gc_row==3?6:0);for(u32 t=0;t<6;t++)if(gc_track==6||gc_track==t){u32 v=p[off+t];p[off+t]=(u8)clamp((s32)(v<=100?v:0)+delta,0,100);}dirty=1;}}
 repaint();
}
u32 gc_key(const u32*e){if(!e)return gc_previous_key(e);u32 code=e[3],f=e[4];
 if(code==12&&owned_back){if(!(f&1))owned_back=0;return 1;}
 if(code==32&&owned_data){if(f&16){owned_data=0;if(menu&&gc_page)gc_edit=!gc_edit;else if(menu&&!sx_submenu&&!du_page&&!mq_page&&row==9){gc_page=1;gc_row=gc_edit=0;}repaint();}return 1;}
 if(menu&&gc_page){
  if(code==12){if((f&9)==1){if(gc_edit)gc_edit=0;else{gc_page=0;row=9;}owned_back=1;repaint();}return 1;}
  if(code==32){if((f&9)==1)owned_data=1;return 1;}
 }else if(menu&&!sx_submenu&&!du_page&&!mq_page&&row==9&&code==32){
  if((f&9)==1)owned_data=1;
  if((f&16)&&owned_data){owned_data=0;gc_page=1;gc_row=gc_edit=0;repaint();}return 1;
 }
 u32 result=gc_previous_key(e);if(!menu)gc_page=gc_edit=0;return result;
}
u32 gc_encoder(const u32*e){
 if(!menu||!e||e[0]!=0x400fbebc||e[3]!=1)return gc_previous_encoder(e);
 s32 delta=(s32)N(0x4006f73a)(e,1,1);if(!delta)return 1;
 if(gc_page){if(gc_edit)gc_adjust(delta);else{gc_row=(gc_row+(delta>0?1:4))%5;repaint();}return 1;}
 if(!sx_submenu&&!du_page&&!mq_page&&!wf_menu_edit()){row=(row+(delta>0?1:9))%10;repaint();return 1;}
 return gc_previous_encoder(e);
}
u32 gc_draw(u32 view,u32 canvas){if(menu&&gc_page){gc_sub_draw(view,canvas);return 1;}return gc_previous_draw(view,canvas);}
u32 gc_menu_row(void){return gc_row;}u32 gc_menu_edit(void){return gc_edit;}
static void value(u32 index,u32 canvas,u32 x,u32 y){(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);
 if(index==0)N(0x40071a04)(canvas,font,126,y,4,"%s",names[gc_groove<8?gc_groove:0]);
 else if(index==1){if(gc_track<6)N(0x40071a04)(canvas,font,126,y,4,"%u",gc_track+1);else N(0x40071a04)(canvas,font,126,y,4,"%s","All");}
 else if(index==4)N(0x40071a04)(canvas,font,126,y,4,"%d",(s32)gc_strum);
 else if(gc_track==6){u32 first=amount(index==3),same=1;volatile u8*p=header();for(u32 t=1;p&&t<6;t++){u32 n=p[(index==3?6:0)+t];if((n<=100?n:0)!=first)same=0;}if(same)N(0x40071a04)(canvas,font,126,y,4,"%u",first);else N(0x40071a04)(canvas,font,126,y,4,"%s","Mixed");}
 else N(0x40071a04)(canvas,font,126,y,4,"%u",amount(index==3));N(0x40072080)(font);
}
#define GC_VALUE(k) void gc_value##k(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;value(k,c,x,y);}
GC_VALUE(0) GC_VALUE(1) GC_VALUE(2) GC_VALUE(3) GC_VALUE(4)
void gc_root_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);N(0x40071a04)(canvas,font,126,y,4,"%s",">");N(0x40072080)(font);}
static void settings(void){u32 h[4]={0};u8 bytes[20],extra;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/Groove.cfg","r",h)){
  u32 ok=N(0x4007baaa)(bytes,20,h)==20&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);
  if(ok&&bytes[0]=='G'&&bytes[1]=='S'&&bytes[2]==2&&bytes[3]<8&&(s8)bytes[4]>=-80&&(s8)bytes[4]<=80&&bytes[5]==(u8)~bytes[3]&&bytes[6]==(u8)~bytes[4]&&bytes[7]==0xa5){gc_groove=bytes[3];gc_strum=(s8)bytes[4];for(u32 i=0;i<12;i++)gc_amounts[i]=bytes[8+i]<=100?bytes[8+i]:0;}
 }}
 if(dirty&&!playing()){
  bytes[0]='G';bytes[1]='S';bytes[2]=2;bytes[3]=gc_groove;bytes[4]=(u8)gc_strum;bytes[5]=(u8)~bytes[3];bytes[6]=(u8)~bytes[4];bytes[7]=0xa5;for(u32 i=0;i<12;i++)bytes[8+i]=gc_amounts[i];
  if(!N(0x4007bc5e)("/Groove.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,20)&&N(0x4007bb0a)(bytes,20,h)==20&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)dirty=0;}
 }
}
void gc_frame(void){settings();gc_previous_frame();}
