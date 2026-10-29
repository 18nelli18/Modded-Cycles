/* Gestes FX historiques ; seul Global > FX ajoute MST/TRK.
 * Aucun panneau MFX par piste : choix et parametres suivent la piste choisie.
 */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 mf_mode,mf_requested,ch_mode,cr_mode,menu,row,gc_level,gc_tree_cursor,sx_submenu,du_page,mq_page,gc_page;
extern volatile u8 mf_live[48];
extern u32 fx_menu_open,fx_menu_slot,fx_menu_cursor;
extern volatile u32 fx_dirty;
extern const u32 fx_rev_order[9],pots_del_order[8];
#ifdef MF_NO_VINYL
extern const u32 nv_rev_order[8];extern volatile u32 fx_dirty;
#define MF_REV_ORDER nv_rev_order
#define MF_REV_COUNT 8
#else
#define MF_REV_ORDER fx_rev_order
#define MF_REV_COUNT 9
#endif
extern u32 mf_old_fx_key(u32*),mf_old_fx_encoder(u32,const u32*),mf_old_gc_key(const u32*),mf_old_gc_encoder(const u32*),mf_old_gc_draw(u32,u32),mf_old_tree_edit(void),mf_fx_selected(void);
extern void mf_old_commit(void),mf_old_value(u32,u32*,const char**,const char**),mf_show(u32),mf_redraw(void),mf_global_draw(u32,u32),mf_frame(void),mf_commit(void),mf_legacy_capture(void),mf_touch(void),mf_mode_set(u32),mf_choose(u32,u32,u32),mf_config_set(u32,u32,u32);
extern u32 mf_choice(u32,u32);
extern volatile u32 mf_wf_api[];
extern void mf_seed_pots(void);
static u32 global_edit,owned_data,owned_back,popup_type,popup_field,popup_index,menu_track=6;
static s32 motion;
static u32 held(u32 key){return !!N(0x4007faf4)(key);}
static u32 child(void){return sx_submenu||du_page||mq_page||gc_page;}
static u32 global(void){return menu&&gc_level==1&&!child();}
static s32 clamp(s32 x,s32 lo,s32 hi){return x<lo?lo:x>hi?hi:x;}
/* Les handlers historiques ne connaissent pas encore le nouvel ID12. Leur
 * presenter Delay garde les vrais Time/Fdbk et tous les autres gestes FX. */
static u32 old_fx_encoder(u32 view,const u32*e){u32 mode=cr_mode;if(mode==12)cr_mode=0;u32 r=mf_old_fx_encoder(view,e);if(mode==12&&cr_mode==0)cr_mode=12;mf_legacy_capture();return r;}
u32 mf_tree_edit(void){return global()&&gc_tree_cursor==9?global_edit:mf_old_tree_edit();}
void mf_global_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);N(0x40071a04)(canvas,font,122,y,4,"%s",mf_mode?"TRK":"MST");N(0x40072080)(font);}
u32 mf_gc_key(const u32*e){
 if(!e)return mf_old_gc_key(e);if(!menu)global_edit=0;
 u32 key=e[3],flags=e[4];
 if(key==12&&owned_back){if(!(flags&1))owned_back=0;return 1;}
 if(key==32&&owned_data){if(flags&16){owned_data=0;global_edit=!global_edit;mf_redraw();}return 1;}
 if(global()&&gc_tree_cursor==9){
  if(key==32){if((flags&9)==1)owned_data=1;return 1;}
  if(key==12&&(flags&9)==1&&global_edit){global_edit=0;owned_back=1;mf_redraw();return 1;}
  if(key!=12){u32 saved=gc_tree_cursor;gc_tree_cursor=0;u32 result=mf_old_gc_key(e);if(gc_level==1)gc_tree_cursor=saved;return result;}
 }
 return mf_old_gc_key(e);
}
u32 mf_gc_encoder(const u32*e){
 if(global()&&e&&e[0]==0x400fbebc&&e[3]==1){
  s32 delta=(s32)N(0x4006f73a)(e,1,1);if(!delta)return 1;
  if(gc_tree_cursor==9&&global_edit){mf_mode_set(delta>0?1:0);mf_redraw();return 1;}
  if(!mf_old_tree_edit()){
   gc_tree_cursor=(gc_tree_cursor+(delta>0?1:9))%10;static const u8 rows[10]={0,1,2,3,4,5,8,9,10,11};row=rows[gc_tree_cursor];mf_redraw();return 1;
  }
 }
 return mf_old_gc_encoder(e);
}
u32 mf_gc_draw(u32 view,u32 canvas){if(global()){mf_global_draw(view,canvas);return 1;}return mf_old_gc_draw(view,canvas);}
u32 mf_fx_encoder(u32 view,const u32*e){
 if(!e||e[0]!=0x400fbebc||menu){popup_type=0;return old_fx_encoder(view,e);}
 u32 knob=e[3],track=mf_fx_selected();if(track>5||(knob!=14&&knob!=15)||held(8)){popup_type=0;return old_fx_encoder(view,e);}
 u32 func=held(1),tr=held(2),settings=held(13),slot=knob==15;
 if(tr&&!func&&!settings){
  s32 delta=(s32)N(0x4006f73a)(e,1,1);u32 count=slot?8:MF_REV_COUNT,current=mf_mode?mf_choice(slot,track):slot?cr_mode:ch_mode;const u32*order=slot?pots_del_order:MF_REV_ORDER;
  if(!fx_menu_open||fx_menu_slot!=slot||menu_track!=track){fx_menu_open=1;fx_menu_slot=slot;menu_track=track;fx_menu_cursor=0;for(u32 i=0;i<count;i++)if(order[i]==current)fx_menu_cursor=i;motion=0;}
  if(delta){s32 sign=delta>0?1:-1;if(motion*sign<0)motion=0;motion+=sign;if(motion>=2||motion<=-2){motion=0;fx_menu_cursor=(u32)clamp((s32)fx_menu_cursor+sign,0,(s32)count-1);}}
  mf_redraw();return 1;
 }
 if(fx_menu_open)return 1;
 if(!mf_mode){popup_type=0;return old_fx_encoder(view,e);}
 u32 type=slot?mf_live[6+track]:mf_live[track],index=0,field=0;
 if(!type){popup_type=0;return old_fx_encoder(view,e);}
 if(!slot){
  if(type==1||type==2){index=func||settings;field=index?4:3;}
  else if(type==3){index=func&&tr?2:func||settings?1:0;field=6+index;}
  else {index=func||settings;field=index?13:12;}
 }else if(type==3){type=5;index=(settings||(func&&tr))?2:func?1:0;field=14+index;}
 else {type=6;index=func||settings;field=index?1:0;}
 if(settings&&mf_wf_api[5])*(volatile u32*)mf_wf_api[5]=1;
 s32 delta=(s32)N(0x4006f73a)(e,1,1);u32 lo=type==6&&index==1?2:0,hi=type==6&&index==1?16:127;
 if(delta)mf_config_set(type,index,(u32)clamp((s32)mf_live[12+4*(type-1)+index]+delta,(s32)lo,(s32)hi));
 popup_type=type;popup_field=field;popup_index=index;mf_show(field);return 1;
}
/* Le compilateur a integre le commit historique dans fx_key. Consommer le
 * menu avant cet appel conserve ses touches, sans ecrire le type global. */
extern volatile u32 dx_other_keys;
extern u32 fx_query_original(u32);
u32 mf_fx_key(u32*e){
 /* Une release longue/consommee peut manquer au compteur evenementiel DX.
  * Reconciler uniquement ses bits deja actifs avec les touches physiques. */
 if(e&&e[3]==1&&dx_other_keys){u32 mask=dx_other_keys;for(u32 key=2;key<32;key++)if((mask&(1u<<key))&&!fx_query_original(key))mask&=~(1u<<key);dx_other_keys=mask;}
 if(e&&e[3]==2&&!(e[4]&1)&&fx_menu_open)mf_commit();return mf_old_fx_key(e);
}
void mf_commit(void){
 if(!mf_mode){if(!fx_menu_open)return;u32 slot=fx_menu_slot,count=slot?8:MF_REV_COUNT;if(fx_menu_cursor<count){u32 value=(slot?pots_del_order:MF_REV_ORDER)[fx_menu_cursor];if(slot){cr_mode=value;if(value==12)mf_seed_pots();}else ch_mode=value;fx_dirty=1;}fx_menu_open=0;mf_redraw();mf_legacy_capture();return;}
 if(!fx_menu_open)return;u32 slot=fx_menu_slot,count=slot?8:MF_REV_COUNT,cursor=fx_menu_cursor,track=menu_track<6?menu_track:mf_fx_selected();if(cursor<count&&track<6)mf_choose(slot,track,(slot?pots_del_order:MF_REV_ORDER)[cursor]);fx_menu_open=0;mf_redraw();
}
void mf_value(u32 field,u32*value,const char**type,const char**label){
 if(!mf_mode||!popup_type||field!=popup_field){mf_old_value(field,value,type,label);return;}
 static const char*names[7]={"","Chorus 1","Chorus 2","Vinyl","Ring Mod","Phaser","Crusher"};
 static const char*labels[7][3]={{"","",""},{"Speed","Depth",""},{"Speed","Depth",""},{"Crackle","Warble Amt","Warble Spd"},{"Frequency","Depth",""},{"Rate","Depth","Feedback"},{"Rate","Bits",""}};
 *value=mf_live[12+4*(popup_type-1)+popup_index];*type=names[popup_type];*label=labels[popup_type][popup_index];
}
