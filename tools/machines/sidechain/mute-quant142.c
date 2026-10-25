/* QntM : mute/solo sur une fraction du pattern, natif immediat par defaut.
 * Setter UI conserve ses autres notifications ; IRQ ne copie que deux mots.
 * Aucun fichier, allocation ou appel UI dans le chemin audio. */
typedef unsigned int u32;typedef int s32;typedef unsigned short u16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#define MUTE (*(volatile u32*)0x800017ac)
#define SOLO (*(volatile u32*)0x800017b0)
extern volatile u32 menu,row,sx_submenu,du_page;
extern u32 wf_menu_edit(void),mq_native_set(u32);
extern u32 mq_previous_key(const u32*),mq_previous_encoder(const u32*),mq_previous_draw(u32,u32);
extern void mq_previous_frame(void),mq_root_draw(u32,u32),mq_sub_draw(u32,u32);
volatile u32 mq_enabled,mq_division=2,mq_page,mq_row,mq_edit;
static volatile u32 pending,want_mute,want_solo;
static u32 previous_step,previous_phase,previous_pattern,seen,dirty,loaded,owned_back,owned_data;
static const u32 divisions[5]={16,8,4,2,1};
static const char*names[5]={"1/16","1/8","1/4","1/2","1"};
static u32 playing(void){return (*(volatile u32*)0x40a78874|*(volatile u32*)0x40a7883c)==1;}
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
static u32 lock(void){u32 sr;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");return sr;}
static void unlock(u32 sr){__asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");}
static void commit(void){if(pending){MUTE=want_mute;SOLO=want_solo;pending=0;}}
static u32 position(u32*length,u32*identity){u32 p=*(volatile u32*)0x40a7887c;
 *identity=p?*(volatile u32*)(p+30706):~0u;
 *length=p?*(volatile u16*)(p+30662):16;
 if(!*length||*length>1024)*length=16;
 return *(volatile u32*)0x40a788ac;
}
/* Appele juste avant les lectures mute/solo de l'IRQ native. */
void mq_tick(void){
 if(!mq_enabled){if(pending)commit();seen=0;return;}
 if(!playing()){commit();seen=0;return;}
 u32 length,pattern,step=position(&length,&pattern),phase=step%length;
 u32 count=divisions[mq_division<5?mq_division:2];
 if(seen&&(step!=previous_step||pattern!=previous_pattern)){
  u32 crossed=pattern!=previous_pattern||phase<previous_phase||phase*count/length!=previous_phase*count/length;
  if(crossed)commit();
 }
 previous_step=step;previous_phase=phase;previous_pattern=pattern;seen=1;
}
u32 mq_set(u32 state){
 if(!mq_enabled||!playing()){pending=0;seen=0;return mq_native_set(state);}
 u32 muted=*(volatile u32*)(state+20),solo=*(volatile u32*)(state+24),sr=lock();
 want_mute=muted;want_solo=solo;pending=(muted!=MUTE||solo!=SOLO);
 if(!seen){u32 length,pattern;previous_step=position(&length,&pattern);previous_phase=previous_step%length;previous_pattern=pattern;seen=1;}
 unlock(sr);
 /* Suite exacte du setter : les six autres flags de piste restent copies. */
 return N(0x4008a4a2)(state);
}
static void changed(void){dirty=1;u32 sr=lock();if(!mq_enabled)commit();seen=0;unlock(sr);repaint();}
u32 mq_key(const u32*e){if(!e)return 0;u32 code=e[3],f=e[4];
 if(code==12&&owned_back){if(!(f&1))owned_back=0;return 1;}
 if(menu&&mq_page){
  if(code==12){if((f&9)==1){if(mq_edit)mq_edit=0;else{mq_page=0;row=8;}owned_back=1;repaint();}return 1;}
  if(code==32){if((f&9)==1)owned_data=1;if((f&16)&&owned_data){owned_data=0;if(!mq_row){mq_enabled=!mq_enabled;changed();}else{mq_edit=!mq_edit;repaint();}}return 1;}
 }else if(menu&&!sx_submenu&&!du_page&&row==8&&code==32){if((f&9)==1)owned_data=1;if((f&16)&&owned_data){owned_data=0;mq_page=1;mq_row=mq_edit=0;repaint();}return 1;}
 u32 result=mq_previous_key(e);if(!menu)mq_page=mq_edit=0;return result;
}
u32 mq_encoder(const u32*e){
 if(!menu||!e||e[0]!=0x400fbebc||e[3]!=1)return mq_previous_encoder(e);
 s32 delta=(s32)N(0x4006f73a)(e,1,1);if(!delta)return 1;
 if(mq_page){if(!mq_edit)mq_row=(mq_row+1)%2;else{int value=(int)mq_division+(delta>0?1:-1);if(value<0)value=0;if(value>4)value=4;mq_division=(u32)value;changed();}repaint();return 1;}
 if(!sx_submenu&&!du_page&&!wf_menu_edit()){row=(row+(delta>0?1:8))%9;repaint();return 1;}
 return mq_previous_encoder(e);
}
u32 mq_draw(u32 view,u32 canvas){if(menu&&mq_page){mq_sub_draw(view,canvas);return 1;}return mq_previous_draw(view,canvas);}
u32 mq_menu_row(void){return mq_row;}u32 mq_menu_edit(void){return mq_edit;}
void mq_root_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);N(0x40071a04)(canvas,font,126,y,4,"%s",mq_enabled?"On >":"Off >");N(0x40072080)(font);}
static void value(u32 index,u32 canvas,u32 x,u32 y){(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);N(0x40071a04)(canvas,font,126,y,4,"%s",index?names[mq_division<5?mq_division:2]:(mq_enabled?"On":"Off"));N(0x40072080)(font);}
void mq_value0(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;value(0,c,x,y);}
void mq_value1(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;value(1,c,x,y);}
/* Preferences globales : fichier court garde, lecture/ecriture UI seulement. */
static void settings(void){u32 h[4]={0};u8 bytes[8],extra;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/MuteQuant.cfg","r",h)){
  u32 ok=N(0x4007baaa)(bytes,8,h)==8&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);
  if(ok&&bytes[0]=='Q'&&bytes[1]=='M'&&bytes[2]==1&&bytes[3]<2&&bytes[4]<5&&bytes[5]==(u8)~bytes[3]&&bytes[6]==(u8)~bytes[4]&&bytes[7]==0xa5){mq_enabled=bytes[3];mq_division=bytes[4];}
 }}
 if(dirty&&!playing()){
  bytes[0]='Q';bytes[1]='M';bytes[2]=1;bytes[3]=(u8)mq_enabled;bytes[4]=(u8)mq_division;bytes[5]=(u8)~bytes[3];bytes[6]=(u8)~bytes[4];bytes[7]=0xa5;
  if(!N(0x4007bc5e)("/MuteQuant.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(bytes,8,h)==8&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)dirty=0;}
 }
}
void mq_frame(void){settings();if(!playing()){u32 sr=lock();commit();seen=0;unlock(sr);}mq_previous_frame();}
