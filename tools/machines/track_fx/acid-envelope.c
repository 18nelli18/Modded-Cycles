/* Preference ACID unique pour toutes les pistes. E/S reservees au service UI au repos.
 * Aucun p-lock ajoute ; les sons et projets natifs gardent leur format. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 menu,row,gc_level,gc_tree_cursor,gc_page,sx_submenu,du_page,mq_page;
extern u32 gc_input_quiet(void),mf_tree_edit(void);
extern u32 mf_gc_key(const u32*),mf_gc_encoder(const u32*),mf_gc_draw(u32,u32);
extern void mf_frame(void);
volatile u32 ae_mode,ae_edit;
static u32 dirty,loaded,changed,owned_data,owned_back;
static const u8 order[3]={1,0,2};
static const char*names[3]={"F","A","AF"};
static u32 global_menu(void){return menu&&gc_level==1&&!gc_page&&!sx_submenu&&!du_page&&!mq_page;}
static void redraw(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
void ae_set(u32 mode){if(mode<3){ae_mode=mode;changed=1;dirty=1;}}
u32 ae_global_edit(void){return global_menu()&&gc_tree_cursor==10?ae_edit:mf_tree_edit();}
void ae_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){
 (void)a;(void)b;(void)x;u32 font[2],m=ae_mode;
 N(0x40072260)(font,0x40140ab0);N(0x40071a04)(canvas,font,122,y,4,"%s",names[m<3?m:0]);N(0x40072080)(font);
}
u32 ae_key(const u32*e){
 if(!menu)ae_edit=0;if(!e)return mf_gc_key(e);
 u32 code=e[3],flags=e[4];
 if(code==12&&owned_back){if(!(flags&1))owned_back=0;return 1;}
 if(code==32&&owned_data){if(flags&16){owned_data=0;if(global_menu()&&gc_tree_cursor==10){ae_edit=!ae_edit;redraw();}}return 1;}
 if(global_menu()&&gc_tree_cursor==10){
  if(code==32){if((flags&9)==1)owned_data=1;return 1;}
  if(code==12&&(flags&9)==1&&ae_edit){ae_edit=0;owned_back=1;redraw();return 1;}
 }
 return mf_gc_key(e);
}
u32 ae_encoder(const u32*e){
 if(global_menu()&&e&&e[0]==0x400fbebc&&e[3]==1){
  s32 delta=(s32)N(0x4006f73a)(e,1,1);if(!delta)return 1;
  if(gc_tree_cursor==10&&ae_edit){
   u32 m=ae_mode,i=m==1?0:m==2?2:1;s32 next=(s32)i+(delta>0?1:-1);if(next<0)next=0;if(next>2)next=2;ae_set(order[next]);
   redraw();return 1;
  }
  if(!ae_global_edit()){static const u8 rows[11]={0,1,2,3,4,5,8,9,10,11,12};gc_tree_cursor=(gc_tree_cursor+(delta>0?1:10))%11;row=rows[gc_tree_cursor];redraw();return 1;}
 }
 return mf_gc_encoder(e);
}
u32 ae_draw(u32 view,u32 canvas){return mf_gc_draw(view,canvas);}
void ae_service(void){
 u32 h[4]={0};u8 b[18]={0},extra;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/AcidEnv.cfg","r",h)){
  u32 n=N(0x4007baaa)(b,18,h),ok=!N(0x4007baaa)(&extra,1,h),mode=0;N(0x4007bc1c)(h);
  if(n==8){
   ok=ok&&b[0]=='A'&&b[1]=='E'&&b[2]==2&&b[3]==1&&b[4]<3&&b[5]==(u8)~b[4]&&b[6]==165&&b[7]==90;mode=b[4];
  }else if(n==18){
   /* Ancien prototype : migrer une valeur commune ; sinon choisir F. */
   ok=ok&&b[0]=='A'&&b[1]=='E'&&b[2]==1&&b[3]==6&&b[16]==165&&b[17]==90;
   u32 same=1;for(u32 i=0;i<6;i++){if(b[4+i]>2||b[10+i]!=(u8)~b[4+i])ok=0;if(b[4+i]!=b[4])same=0;}
   mode=same?b[4]:0;if(ok)dirty=1;
  }else ok=0;
  if(ok&&!changed)ae_mode=mode;
 }}
 if(!menu)ae_edit=0;
 if(dirty&&gc_input_quiet()&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c){
  b[0]='A';b[1]='E';b[2]=2;b[3]=1;b[4]=ae_mode;b[5]=~b[4];b[6]=165;b[7]=90;
  if(!N(0x4007bc5e)("/AcidEnv.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(b,8,h)==8&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)dirty=0;}
 }
}
void ae_frame(void){ae_service();mf_frame();}
