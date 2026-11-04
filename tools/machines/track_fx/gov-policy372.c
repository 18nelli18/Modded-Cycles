/* GOV global : choix rare du regulateur, UI native et E/S uniquement a l arret. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 menu,row,gc_level,gc_tree_cursor,gc_page,sx_submenu,du_page,mq_page;
extern u32 gp_old_edit(void),gp_old_key(const u32*),gp_old_encoder(const u32*),gc_input_quiet(void);
extern void gp_old_frame(void);
volatile u32 gp_mode;
static u32 edit,owned,back,loaded,dirty,changed;
static u32 global(void){return menu&&gc_level==1&&!gc_page&&!sx_submenu&&!du_page&&!mq_page;}
static void redraw(void){u32 a=*(volatile u32*)0x40fe4178;if(a)N(0x40076bee)(a+64);}
u32 gp_edit(void){return global()&&gc_tree_cursor==GP_ROW?edit:gp_old_edit();}
void gp_set(u32 v){if(v<2){gp_mode=v;dirty=changed=1;}}
void gp_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;(void)x;u32 f[2];N(0x40072260)(f,0x40140ab0);N(0x40071a04)(canvas,f,122,y,4,"%s",gp_mode?"Trk":"Lod");N(0x40072080)(f);}
u32 gp_key(const u32*e){
 if(!menu)edit=0;if(!e)return gp_old_key(e);u32 k=e[3],f=e[4];
 if(k==32&&owned){if(f&16){owned=0;if(global()&&gc_tree_cursor==GP_ROW){edit=!edit;redraw();}}return 1;}
 if(k==12&&back){if(!(f&1))back=0;return 1;}
 if(global()&&gc_tree_cursor==GP_ROW){
  if(k==32){if((f&9)==1)owned=1;return 1;}
  if(k==12&&(f&9)==1&&edit){edit=0;back=1;redraw();return 1;}
  u32 prior=gc_tree_cursor;gc_tree_cursor=0;u32 result=gp_old_key(e);if(gc_level==1)gc_tree_cursor=prior;return result;
 }
 return gp_old_key(e);
}
u32 gp_encoder(const u32*e){
 if(global()&&e&&e[0]==0x400fbebc&&e[3]==1){
  s32 d=(s32)N(0x4006f73a)(e,1,1);if(!d)return 1;
  if(gc_tree_cursor==GP_ROW&&edit){gp_set(d>0);redraw();return 1;}
  if(!gp_edit()){
   if(gc_tree_cursor==GP_ROW){gc_tree_cursor=d>0?0:GP_ROW-1;row=d>0?0:GP_ROW;redraw();return 1;}
   if((gc_tree_cursor==0&&d<0)||(gc_tree_cursor==GP_ROW-1&&d>0)){gc_tree_cursor=GP_ROW;row=0;redraw();return 1;}
  }
 }
 return gp_old_encoder(e);
}
void gp_service(void){
 volatile u32 h[4];volatile u8 b[8];u8 extra;for(u32 i=0;i<4;i++)h[i]=0;for(u32 i=0;i<8;i++)b[i]=0;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/Governor.cfg","r",h)){u32 n=N(0x4007baaa)(b,8,h),ok=!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);if(n==8&&ok&&b[0]=='G'&&b[1]=='V'&&b[2]==1&&b[3]==1&&b[4]<2&&b[5]==(u8)~b[4]&&b[6]==165&&b[7]==90&&!changed)gp_mode=b[4];}}
 if(!menu)edit=0;
 if(dirty&&gc_input_quiet()&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c){b[0]='G';b[1]='V';b[2]=b[3]=1;b[4]=gp_mode;b[5]=~b[4];b[6]=165;b[7]=90;
  if(!N(0x4007bc5e)("/Governor.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(b,8,h)==8&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)dirty=0;}
 }
}
void gp_frame(void){gp_service();gp_old_frame();}
