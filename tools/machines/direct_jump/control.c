/* Global > JUMP : preference unique ; aucune E/S dans le sequenceur. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 menu,row,gc_level,gc_tree_cursor,gc_page,sx_submenu,du_page,mq_page;
extern volatile u32 jp_enabled,jp_request,jp_fix;extern volatile unsigned short jp_keep;
extern u32 gc_input_quiet(void),jp_old_edit(void),jp_old_key(const u32*),jp_old_encoder(const u32*),jp_old_draw(u32,u32);
extern void jp_old_frame(void),jp_global_draw(u32,u32);
static u32 edit,dirty,loaded,changed,owned_data,owned_back;
static u32 global(void){return menu&&gc_level==1&&!gc_page&&!sx_submenu&&!du_page&&!mq_page;}
static void redraw(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
void jp_set(u32 v){if(v<2){jp_enabled=v;changed=dirty=1;if(!v){jp_request=jp_fix=0;jp_keep=0;}}}
u32 jp_edit(void){return global()&&gc_tree_cursor==JP_ROW?edit:jp_old_edit();}
void jp_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);N(0x40071a04)(canvas,font,122,y,4,"%s",jp_enabled?"ON":"OFF");N(0x40072080)(font);}
u32 jp_key(const u32*e){
 if(!menu)edit=0;if(!e)return jp_old_key(e);u32 code=e[3],flags=e[4];
 if(code==12&&owned_back){if(!(flags&1))owned_back=0;return 1;}
 if(code==32&&owned_data){if(flags&16){owned_data=0;if(global()&&gc_tree_cursor==JP_ROW){edit=!edit;redraw();}}return 1;}
 if(global()&&gc_tree_cursor==JP_ROW){
  if(code==32){if((flags&9)==1)owned_data=1;return 1;}
  if(code==12&&(flags&9)==1&&edit){edit=0;owned_back=1;redraw();return 1;}
  if(code!=12){u32 saved=gc_tree_cursor;gc_tree_cursor=0;u32 r=jp_old_key(e);if(gc_level==1)gc_tree_cursor=saved;return r;}
 }
 return jp_old_key(e);
}
u32 jp_encoder(const u32*e){
 if(global()&&e&&e[0]==0x400fbebc&&e[3]==1){
  s32 delta=(s32)N(0x4006f73a)(e,1,1);if(!delta)return 1;
  if(gc_tree_cursor==JP_ROW&&edit){jp_set(delta>0);redraw();return 1;}
  if(!jp_edit()){static const u8 rows[12]={0,1,2,3,4,5,8,9,10,11,12,13};gc_tree_cursor=(gc_tree_cursor+(delta>0?1:JP_ROW))%(JP_ROW+1);row=rows[gc_tree_cursor];redraw();return 1;}
 }
 return jp_old_encoder(e);
}
u32 jp_draw(u32 view,u32 canvas){if(global()){jp_global_draw(view,canvas);return 1;}return jp_old_draw(view,canvas);}
void jp_service(void){
 u32 h[4]={0};u8 b[8]={0},extra;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/DirectJump.cfg","r",h)){
  u32 n=N(0x4007baaa)(b,8,h),ok=!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);
  if(n==8&&ok&&b[0]=='D'&&b[1]=='J'&&b[2]==1&&b[3]==1&&b[4]<2&&b[5]==(u8)~b[4]&&b[6]==165&&b[7]==90&&!changed)jp_enabled=b[4];
 }}
 if(!menu)edit=0;
 if(dirty&&gc_input_quiet()&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c){
  b[0]='D';b[1]='J';b[2]=b[3]=1;b[4]=jp_enabled;b[5]=~b[4];b[6]=165;b[7]=90;
  if(!N(0x4007bc5e)("/DirectJump.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(b,8,h)==8&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)dirty=0;}
 }
}
void jp_frame(void){jp_service();jp_old_frame();}
