/* Song : DATA ligne, PITCH pattern, DECAY repetitions, TRIG1..6 mutes.
 * PAGE ajoute ; FUNC+PAGE retire ; FUNC+DATA choisit STOP/LOOP. */
#include "song.h"
typedef song_u32 u32;typedef int s32;
#ifndef SONG_ROW
#define SONG_ROW 12
#endif
#define N(a) ((u32(*)())(a))
extern song sg_song;extern volatile u32 sg_active,sg_current,sg_end;
extern volatile u32 menu,row,gc_level,gc_tree_cursor,gc_page,sx_submenu,du_page,mq_page;
extern u32 jp_key(const u32*),jp_encoder(const u32*),jp_draw(u32,u32),jp_edit(void),sg_start(void);
extern void sg_grid_draw(u32,u32),sg_top_draw(u32,u32);
extern void sg_cancel(void),sg_sync(void),sg_global_draw(u32,u32),sg_editor_draw(u32,u32),fx_notice(const char*);
volatile u32 sg_page,sg_cursor;
static u32 owned;
static u32 global(void){return menu&&gc_level==1&&!gc_page&&!sx_submenu&&!du_page&&!mq_page;}
static u32 playing(void){return *(volatile u32*)0x40a78874||*(volatile u32*)0x40a7883c;}
static void redraw(void){u32 a=*(volatile u32*)0x40fe4178;if(a)N(0x40076bee)(a+64);}
u32 sg_menu_row(void){return sg_cursor;}u32 sg_menu_edit(void){return 0;}u32 sg_menu_count(void){return sg_song.count;}
u32 sg_edit(void){return global()&&gc_tree_cursor==SONG_ROW?0:jp_edit();}
void sg_root_value(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;(void)x;u32 f[2];N(0x40072260)(f,0x40140ab0);N(0x40071a04)(c,f,122,y,4,"%s",sg_song.loop?"LOOP >":"STOP >");N(0x40072080)(f);}
void sg_row_value(u32 index,u32 canvas,u32 y){
 if(index>=sg_song.count)return;const song_row*r=&sg_song.rows[index];char mute[7];for(u32 t=0;t<6;t++)mute[t]=(r->mutes&(1u<<t))?'-':'1'+t;mute[6]=0;
 u32 f[2];N(0x40072260)(f,0x40140ab0);N(0x40071a04)(canvas,f,126,y,4,"%c%02d x%d %s",'A'+r->pattern/16,1+r->pattern%16,r->repeats,mute);N(0x40072080)(f);
}
static u32 delegate(const u32*e){u32 saved=gc_tree_cursor;gc_tree_cursor=0;u32 r=jp_key(e);if(gc_level==1)gc_tree_cursor=saved;return r;}
u32 sg_key(const u32*e){
 if(!e)return jp_key(e);u32 code=e[3],flags=e[4],press=(flags&9)==1;
 if(!menu)sg_page=0;
 if(!sg_page){
  if(menu&&!gc_level&&gc_tree_cursor==2&&code==32){if(press)owned=1;if((flags&16)&&owned){owned=0;sg_sync();if(!sg_song.count){sg_song.count=1;sg_song.rows[0]=(song_row){0,1,0,0};}sg_page=1;sg_cursor=0;redraw();}return 1;}
  return jp_key(e);
 }
 if(code==12){if(press){sg_page=0;redraw();}return 1;}
 if(code==10){if(press&&!playing()&&!sg_active&&!sg_start()){fx_notice("Song: 64 plays max");return 1;}return delegate(e);}
 if(code==11){if(press&&!playing())sg_cancel();return delegate(e);}
 if(code==32){if(press&&N(0x4007faf4)(1)&&!playing()){sg_song.loop=!sg_song.loop;fx_notice(sg_song.loop?"Song LOOP":"Song STOP");redraw();}return 1;}
 if(code==15){if(press&&!playing()&&!sg_active){if(N(0x4007faf4)(1)){if(sg_song.count>1){for(u32 i=sg_cursor;i+1<sg_song.count;i++)sg_song.rows[i]=sg_song.rows[i+1];sg_song.count--;if(sg_cursor>=sg_song.count)sg_cursor=sg_song.count-1;}}else if(sg_song.count<64){for(u32 i=sg_song.count;i>sg_cursor+1;i--)sg_song.rows[i]=sg_song.rows[i-1];sg_song.rows[sg_cursor+1]=sg_song.rows[sg_cursor];sg_song.count++;sg_cursor++;}redraw();}return 1;}
 if(code>=16&&code<22){if(press&&!playing()&&!sg_active){sg_song.rows[sg_cursor].mutes^=1u<<(code-16);redraw();}return 1;}
 return delegate(e);
}
u32 sg_encoder(const u32*e){
 if(!e||!menu||e[0]!=0x400fbebc)return jp_encoder(e);s32 d=(s32)N(0x4006f73a)(e,1,1);if(!d)return 1;
 if(sg_page){
  if(e[3]==1){s32 n=(s32)sg_cursor+(d>0?1:-1);if(n<0)n=0;if(n>=(s32)sg_song.count)n=sg_song.count-1;sg_cursor=n;}
  else if((e[3]==2||e[3]==3)&&!playing()&&!sg_active){song_row*r=&sg_song.rows[sg_cursor];s32 n=(e[3]==2?r->pattern:r->repeats)+d,lo=e[3]==2?0:1,hi=e[3]==2?95:64;if(n<lo)n=lo;if(n>hi)n=hi;if(e[3]==2)r->pattern=n;else r->repeats=n;}
  else return 1;redraw();return 1;
 }
 if(!gc_level&&!gc_page&&!sx_submenu&&!du_page&&!mq_page&&e[3]==1){gc_tree_cursor=(gc_tree_cursor+(d>0?1:2))%3;row=0;redraw();return 1;}return jp_encoder(e);
}
u32 sg_draw(u32 view,u32 canvas){if(menu&&sg_page){sg_grid_draw(view,canvas);return 1;}if(menu&&!gc_level&&!gc_page&&!sx_submenu&&!du_page&&!mq_page){u32 saved=gc_tree_cursor;gc_tree_cursor=0;jp_draw(view,canvas);gc_tree_cursor=saved;sg_top_draw(view,canvas);return 1;}return jp_draw(view,canvas);}

