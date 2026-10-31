/* Preference globale Mac, directement sous Pad, et sauvegarde UI au repos. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 mb_silent,menu,row,gc_level,gc_tree_cursor,gc_page,sx_submenu,du_page,mq_page;
extern u32 mb_old_key(const u32*),mb_old_encoder(const u32*),mb_old_draw(u32,u32),mb_old_edit(void),gc_input_quiet(void);
extern void mb_old_frame(void),mb_global_draw(u32,u32),mb_cancel(void);
static u32 edit,owned,back,loaded,dirty,changed;
static u32 global(void){return menu&&gc_level==1&&!gc_page&&!sx_submenu&&!du_page&&!mq_page;}
static void redraw(void){u32 a=*(volatile u32*)0x40fe4178;if(a)N(0x40076bee)(a+64);}
u32 mb_tree_row(void){return gc_tree_cursor;}
u32 mb_edit(void){if(global()&&gc_tree_cursor==1)return edit;u32 saved=gc_tree_cursor;if(global()&&saved>1)gc_tree_cursor--;u32 result=mb_old_edit();gc_tree_cursor=saved;return result;}
void mb_set(u32 value){if(value<2){mb_silent=value;changed=dirty=1;mb_cancel();}}
void mb_value(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);N(0x40071a04)(c,font,122,y,4,"%s",mb_silent?"Sil":"Stk");N(0x40072080)(font);}
u32 mb_gc_key(const u32*e){
 if(!menu)edit=0;if(!e)return mb_old_key(e);u32 code=e[3],flags=e[4];
 if(code==12&&back){if(!(flags&1))back=0;return 1;}
 if(code==32&&owned){if(flags&16){owned=0;if(global()&&gc_tree_cursor==1){edit=!edit;redraw();}}return 1;}
 if(global()&&gc_tree_cursor==1){if(code==32){if((flags&9)==1)owned=1;return 1;}if(code==12&&(flags&9)==1&&edit){edit=0;back=1;redraw();return 1;}}
 u32 saved=gc_tree_cursor,translate=global();if(translate)gc_tree_cursor=saved>1?saved-1:0;u32 result=mb_old_key(e);if(translate&&gc_level==1)gc_tree_cursor=saved;return result;
}
u32 mb_gc_encoder(const u32*e){
 if(global()&&e&&e[0]==0x400fbebc&&e[3]==1){s32 d=(s32)N(0x4006f73a)(e,1,1);if(!d)return 1;
  if(gc_tree_cursor==1&&edit){mb_set(d<0?1:0);redraw();return 1;}
  if(!mb_edit()){static const u8 rows[13]={0,0,1,2,3,4,5,8,9,10,11,12,13};gc_tree_cursor=(gc_tree_cursor+(d>0?1:12))%13;row=rows[gc_tree_cursor];redraw();return 1;}
 }
 u32 saved=gc_tree_cursor,translate=global();if(translate)gc_tree_cursor=saved>1?saved-1:0;u32 result=mb_old_encoder(e);if(translate&&gc_level==1)gc_tree_cursor=saved;return result;
}
u32 mb_gc_draw(u32 v,u32 c){if(global()){mb_global_draw(v,c);return 1;}return mb_old_draw(v,c);}
void mb_service(void){
 u32 h[4]={0};u8 b[8]={0},extra;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/MachineBrowse.cfg","r",h)){u32 n=N(0x4007baaa)(b,8,h),ok=!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);if(n==8&&ok&&b[0]=='M'&&b[1]=='B'&&b[2]==1&&b[3]==1&&b[4]<2&&b[5]==(u8)~b[4]&&b[6]==165&&b[7]==90&&!changed)mb_silent=b[4];}}
 if(!menu)edit=0;
 if(dirty&&gc_input_quiet()&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c){b[0]='M';b[1]='B';b[2]=b[3]=1;b[4]=mb_silent;b[5]=~b[4];b[6]=165;b[7]=90;
  if(!N(0x4007bc5e)("/MachineBrowse.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(b,8,h)==8&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)dirty=0;}
 }
}
void mb_frame(void){mb_service();mb_old_frame();}
