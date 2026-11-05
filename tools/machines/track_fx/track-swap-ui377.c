/* Interface Track > Swap : les setters natifs sont notifies apres permutation.
 * Services de sauvegarde existants conserves ; aucun nouveau service periodique.
 */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#include "../song/song.h"
#define N(a) ((u32(*)())(a))
typedef struct {u8 *base;u32 stride,bytes,rows;} ts_block;
typedef struct {u8 *base;u32 stride,rows;} ts_masks;
typedef struct {ts_block *blocks;u32 count;ts_masks *masks;u32 mask_count;const volatile u32*owner;u32 expected_owner,expected_active,expected_generation;} ts_plan;
extern u32 ts_exchange(const ts_plan*,u32,u32),ts_bits(u32,u32,u32);
extern u32 ts_old_key(const u32*),ts_old_encoder(const u32*),sx_track(void);
extern u32 ts_tree_edit(void);
extern volatile u32 menu,row,gc_level,gc_tree_cursor,gc_page,sx_submenu,du_page,mq_page;
extern void ts_track_menu(u32,u32),ts_page_menu(u32,u32),ts_notice(const char*);
extern void ts_capture_lfo(void),ts_capture_extra(void),ts_fxp_capture(u8*),ts_fxd_apply(const u8*);
extern volatile u8 ts_scramble_masks[6],ts_duck_config[6][5],ts_duck_fx[6];
extern u32 ts_filter_get(u32);extern void ts_filter_set(u32,u32);
extern volatile u32 ts_lfo_context,ts_lp_one[6],ts_lp_two[6],ts_extra_contexts[2],ts_extra_polarity[12];
extern volatile u32 ts_glide[6],ts_legato[6],ts_acid_initialized[6],ts_slot[6],ts_mode[6];
#ifdef TS_CHORD
extern u32 ts_ck_read(const u8*,u32),ts_ck_midi_get(u32);
extern void ts_ck_set(u32,u32),ts_ck_midi_set(u32,u32);
#endif
extern volatile u8 ts_mf_live[48];
extern u32 ts_mf_choice(u32,u32);extern void ts_mf_choose(u32,u32,u32),ts_mf_capture(void);
extern volatile u32 ts_mf_mode;
extern song ts_song;
volatile u32 ts_page,ts_row,ts_edit,ts_source,ts_target;
static u32 data_owned,back_owned;
static u32 track_menu(void){return menu&&gc_level==2&&!gc_page&&!sx_submenu&&!du_page&&!mq_page;}
static void redraw(void){u32 a=*(volatile u32*)0x40fe4178;if(a)N(0x40076bee)(a+64);}
static u32 object_data(u32 obj,u32 offset){if(!obj)return 0;u32 vt=*(u32*)obj;if(!vt)return 0;return N(*(u32*)(vt+offset))(obj);}
static void notify(u32 obj){u32 vt=*(u32*)obj;N(*(u32*)(vt+16))(obj,0);}
static void add(ts_block *p,u32*n,u32 base,u32 stride,u32 bytes){p[*n]=(ts_block){(u8*)base,stride,bytes,6};(*n)++;}
static void swap_bytes(u8*p,u32 stride,u32 bytes,u32 a,u32 b){for(u32 i=0;i<bytes;i++){u8 v=p[a*stride+i];p[a*stride+i]=p[b*stride+i];p[b*stride+i]=v;}}
static void ts_fxd_capture(u8*p){ts_fxp_capture(p);for(u32 t=0;t<6;t++){p[36+t]=ts_scramble_masks[t];for(u32 i=0;i<5;i++)p[42+5*t+i]=ts_duck_config[t][i];p[72+t]=ts_duck_fx[t];}}
u32 ts_native_swap(u32 a,u32 b){
 if(a>=6||b>=6||a==b||*(volatile u32*)0x40a7883c||*(volatile u32*)0x40a78874)return 0;
 u32 root=N(0x400cf866)(),pat=root?N(0x4000f208)(root):0,kit=root?N(0x4000eb9c)(root):0;
 if(!pat||!kit)return 0;
 u32 owner=object_data(root,40),generation=*(volatile u32*)0x468f6e80;
 if(!owner||owner<0x40000400u||owner>0x42400000u-0x37615cu)return 0;
 u32 seq[6],snd[6],seqbase=0,sndbase=0,pool=object_data(pat+640,40),kitbase=object_data(kit,52);
 for(u32 t=0;t<6;t++){
  seq[t]=N(0x4000cfcc)(pat,t);snd[t]=N(0x40009c1a)(kit,t);
  u32 q=object_data(seq[t],40),s=object_data(snd[t],40);
  if(!t){seqbase=q;sndbase=s;}
  if(!q||!s||q!=seqbase+722*t||s!=sndbase+100*t)return 0;
 }
 u32 active=*(volatile u32*)0x40a7887c;
 if(!kitbase||sndbase!=kitbase+28||pool!=seqbase+4332||!active)return 0;
 u32 pattern=*(u32*)(seqbase+30706);
 if(pattern>=96||pattern!=*(u32*)(active+30706)||ts_song.count>64)return 0;
 /* Les IDs seuls ne prouvent pas que les objets appartiennent au projet.
  * RawProject :96patterns de30710o puis96kits de7094o. */
 if(seqbase!=owner+28+pattern*30710u||kitbase!=owner+0x2cfc5cu+pattern*7094u)return 0;
 if(active!=0x406fa040u+pattern*30710u||*(const u32*)(owner+8)!=*(volatile u32*)0x406fa02c)return 0;
 ts_block blocks[24];u32 n=0;
 add(blocks,&n,seqbase,722,722);add(blocks,&n,pool,4385,4385);add(blocks,&n,sndbase,100,100);add(blocks,&n,kitbase+16,2,2);
 u32 ctx=ts_lfo_context;
 if(ctx){add(blocks,&n,ctx,32,32);add(blocks,&n,ctx+192,16,16);}
 add(blocks,&n,(u32)ts_lp_one,4,4);add(blocks,&n,(u32)ts_lp_two,4,4);
 for(u32 bank=0;bank<2;bank++)if(ts_extra_contexts[bank]){
  add(blocks,&n,ts_extra_contexts[bank],32,32);add(blocks,&n,ts_extra_contexts[bank]+192,16,16);
 }
 add(blocks,&n,(u32)ts_extra_polarity,4,4);add(blocks,&n,(u32)ts_extra_polarity+24,4,4);
#ifndef TS_STOCK_ONLY
 add(blocks,&n,(u32)ts_glide,4,4);add(blocks,&n,(u32)ts_legato,4,4);add(blocks,&n,(u32)ts_acid_initialized,4,4);
 add(blocks,&n,(u32)ts_slot,4,4);add(blocks,&n,(u32)ts_mode,4,4);
#endif
 add(blocks,&n,(u32)ts_mf_live,1,1);add(blocks,&n,(u32)ts_mf_live+6,1,1);
 /* ChordKeys Optional : passer par son codec compact, sans toucher Page Length. */
#ifdef TS_CHORD
 u32 keys[2]={ts_ck_read((u8*)(seqbase+30642),a),ts_ck_read((u8*)(seqbase+30642),b)};
 u32 midi[2]={ts_ck_midi_get(a),ts_ck_midi_get(b)};
#endif
 u8 fx[78];u32 filters[6];for(u32 t=0;t<6;t++)filters[t]=ts_filter_get(t);ts_fxd_capture(fx);
 ts_plan plan={blocks,n,0,0,(const volatile u32*)(root+16),owner,active,generation};if(!ts_exchange(&plan,a,b))return 0;
 /* Les rangs des masques sont des pistes, ceux de SCRAMBLE des operateurs. */
 for(u32 start=6;start<=12;start+=6)swap_bytes(fx+start,1,1,a,b);
 swap_bytes(fx+21,1,1,a,b);swap_bytes(fx+36,1,1,a,b);swap_bytes(fx+42,5,5,a,b);swap_bytes(fx+72,1,1,a,b);
 for(u32 t=0;t<6;t++)fx[42+5*t]=(u8)ts_bits(fx[42+5*t],a,b);
 for(u32 i=0;i<ts_song.count;i++)if(ts_song.rows[i].pattern==pattern)ts_song.rows[i].mutes=(u8)ts_bits(ts_song.rows[i].mutes,a,b);
 ts_fxd_apply(fx);
 ts_filter_set(a,filters[b]);ts_filter_set(b,filters[a]);
#ifdef TS_CHORD
 ts_ck_set(a,keys[1]);ts_ck_set(b,keys[0]);ts_ck_midi_set(a,midi[1]);ts_ck_midi_set(b,midi[0]);
#endif
 notify(seq[a]);notify(seq[b]);notify(snd[a]);notify(snd[b]);notify(kit);
 ts_mf_capture();if(ts_mf_mode)for(u32 slot=0;slot<2;slot++){ts_mf_choose(slot,a,ts_mf_choice(slot,a));ts_mf_choose(slot,b,ts_mf_choice(slot,b));}
 ts_capture_lfo();ts_capture_extra();redraw();return 1;
}
u32 ts_menu_row(void){return ts_page?ts_row:gc_tree_cursor;}
u32 ts_menu_edit(void){return ts_page&&ts_edit;}
static void value(u32 canvas,u32 y,u32 t){
 u32 f[2];N(0x40072260)(f,0x40140ab0);N(0x40071a04)(canvas,f,122,y,4,"T%u",t+1);N(0x40072080)(f);
}
void ts_source_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;(void)x;value(canvas,y,ts_source);}
void ts_target_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;(void)x;value(canvas,y,ts_target);}
void ts_empty_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){
 (void)a;(void)b;(void)canvas;(void)x;(void)y;
}
void ts_draw(u32 view,u32 canvas){if(!track_menu()||gc_tree_cursor!=3)ts_page=ts_edit=0;if(ts_page)ts_page_menu(view,canvas);else ts_track_menu(view,canvas);}
u32 ts_key(const u32*e){
 if(!track_menu()||gc_tree_cursor!=3){ts_page=ts_edit=0;data_owned=0;}if(!e)return ts_old_key(e);u32 k=e[3],f=e[4];
 if(k==32&&data_owned){if(f&16){data_owned=0;if(ts_page){if(ts_row<2)ts_edit=!ts_edit;else if(ts_native_swap(ts_source,ts_target))ts_notice("Tracks swapped");else ts_notice("Stop first / choose two tracks");}else{ts_page=1;ts_row=ts_edit=0;ts_source=sx_track();ts_target=(ts_source+1)%6;}redraw();}return 1;}
 if(k==12&&back_owned){if(f&16)back_owned=0;return 1;}
 if(ts_page&&menu){
  if(k==32){if((f&9)==1)data_owned=1;return 1;}
  if(k==12&&(f&9)==1){if(ts_edit)ts_edit=0;else ts_page=0;back_owned=1;redraw();return 1;}
  return ts_old_key(e);
 }
 if(track_menu()&&gc_tree_cursor==3){
  if(k==32){if((f&9)==1)data_owned=1;return 1;}
  u32 old=gc_tree_cursor;gc_tree_cursor=0;u32 r=ts_old_key(e);if(gc_level==2)gc_tree_cursor=old;return r;
 }
 return ts_old_key(e);
}
u32 ts_encoder(const u32*e){
 if(e&&e[0]==0x400fbebc&&e[3]==1){s32 d=(s32)N(0x4006f73a)(e,1,1);
  if(ts_page&&menu){if(d){if(ts_edit&&ts_row<2){volatile u32 *v=ts_row?&ts_target:&ts_source;s32 next=(s32)*v+d;*v=next<0?0:next>5?5:(u32)next;}else ts_row=d>0?(ts_row+1)%3:(ts_row+2)%3;redraw();}return 1;}
  /* Ne jamais deleguer une liste de4lignes au compteur historique de3. */
  if(track_menu()&&d&&!ts_tree_edit()){gc_tree_cursor=(gc_tree_cursor+(d>0?1:3))%4;row=6+gc_tree_cursor;redraw();return 1;}
 }
 return ts_old_encoder(e);
}
