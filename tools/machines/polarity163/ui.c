/* Une ligne ajoutee aux menus natifs, memes gestes DATA/BACK. */
typedef unsigned int u32;typedef unsigned char u8;typedef int s32;
#define N(a) ((u32(*)())(a))
extern volatile u32 lp_one[6],lp_two[6],lp_dirty,lf2p_row,lf2p_track,lf2p_edit;
extern u32 lp1_old_count(u32),lp1_old_encoder(u32,const u32*),lp1_old_key(u32,const u32*),lp2_old_encoder(u32,const u32*),sx_track(void);
extern void lp_label(void),lp1_value(u32,u32,u32,u32,u32);
#ifdef LFO_SOUND_POL
extern u32 lp_sound_get(u32,u32);extern void lp_sound_set(u32,u32,u32);
#endif
static u32 lp1_edit,lp1_owned;static u32 lp1_widget[21];
static void redraw(u32 view){N(0x40076082)(view);}
static u32 primary_selected(u32 view){u32*p=(u32*)view;return p[5]+p[6]==lp1_old_count(view);}
u32 lp1_count(u32 view){return lp1_old_count(view)+1;}
u32 lp1_prepare(u32 view){(void)view;for(u32 i=0;i<21;i++)lp1_widget[i]=0;
 lp1_widget[5]=lp1_widget[13]=1;lp1_widget[6]=(u32)lp_label;lp1_widget[14]=(u32)lp1_value;((u8*)lp1_widget)[80]=lp1_edit;return (u32)lp1_widget;}
static void value(u32 bank,u32 canvas,u32 y){u32 t=bank?lf2p_track:sx_track();if(t>5)t=0;
#ifdef LFO_SOUND_POL
 u32 uni=lp_sound_get(t,bank);
#else
 u32 uni=(bank?lp_two:lp_one)[t];
#endif
 N(0x40071a04)(canvas,0x40ea14cc,120,y,4,"%s",uni?"Uni":"Bi");}
void lp1_value(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;(void)x;value(0,c,y);}
void lp2_pol_value(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;(void)x;value(1,c,y);}
u32 lp1_encoder(u32 view,const u32*e){
 if(e&&e[0]==0x400fbebc&&e[3]==1&&primary_selected(view)){
  s32 delta=(s32)N(0x4006f73a)(e,1,1);if(lp1_edit){u32 t=sx_track();if(t<6&&delta){
#ifdef LFO_SOUND_POL
lp_sound_set(t,0,delta>0);
#endif
lp_one[t]=delta>0;lp_dirty=1;}redraw(view);return 1;}
  if(delta>=0)return 1;
 }else lp1_edit=0;
 return lp1_old_encoder(view,e);
}
u32 lp1_key(u32 view,const u32*e){
 if(e&&e[3]==32&&lp1_owned){if(e[4]&16){lp1_owned=0;lp1_edit=!lp1_edit;redraw(view);}return 1;}
 if(e&&primary_selected(view)){
  if(e[3]==32){if((e[4]&9)==1)lp1_owned=1;return 1;}
  if(e[3]==12&&lp1_edit){if((e[4]&9)==1){lp1_edit=0;redraw(view);}return 1;}
 }else lp1_edit=0;
 return lp1_old_key(view,e);
}
u32 lp2_encoder(u32 view,const u32*e){
 if(e&&e[0]==0x400fbebc&&e[3]==1){
  if(lf2p_row==9){s32 delta=(s32)N(0x4006f73a)(e,1,1);
   if(lf2p_edit){if(delta&&lf2p_track<6){
#ifdef LFO_SOUND_POL
lp_sound_set(lf2p_track,1,delta>0);
#endif
lp_two[lf2p_track]=delta>0;lp_dirty=1;}}
   else if(delta<0)lf2p_row=0;redraw(view);return 1;}
  if(lf2p_row==0&&!lf2p_edit&&(s32)N(0x4006f73a)(e,1,1)>0){lf2p_row=9;redraw(view);return 1;}
 }
 return lp2_old_encoder(view,e);
}
extern void lp_frame(void),lp_old_frame(void);
void lp_ui_frame(void){lp_frame();lp_old_frame();}
