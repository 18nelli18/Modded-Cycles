#include "fx.h"
u32 fx_menu_open,fx_menu_slot,fx_menu_cursor,fx_force_active,fx_force_func,fx_force_track,fx_tap_force;
u32 fx_speed=42,fx_depth=64,fx_crackle=24,fx_warble=24,fx_wspeed=32,fx_aux_ch[6],fx_aux_vi[6],fx_dirty;
#ifdef FX_LEAN_FX
/* IDs sauvegardes conserves, seuls les choix presents sont exposes. */
const char *const fx_rev_names[FX_REV_COUNT]={"REVERB","CHORUS 1","CHORUS 2","VINYL",0,0,0,"PS1"};
#ifdef FX_NO_SHIMMER
const u32 fx_rev_order[FX_REV_MENU_COUNT]={7,3,0,1,2};
const char *const fx_del_names[FX_DEL_COUNT]={"DELAY","CRUSH 1","CRUSH 2",0,0,"PING PONG",0,0};
const u32 fx_del_order[FX_DEL_MENU_COUNT]={5,0,1,2};
#else
const char *const fx_del_names[FX_DEL_COUNT]={"DELAY","CRUSH 1","CRUSH 2",0,0,"PING PONG","SHIMMER 1",0};
const u32 fx_rev_order[FX_REV_MENU_COUNT]={7,3,0,1,2},fx_del_order[FX_DEL_MENU_COUNT]={6,5,2,1,0};
#endif
#else
const char *const fx_rev_names[FX_REV_COUNT]={"REVERB","CHORUS 1","CHORUS 2","VINYL","VINYL+REV","CHOR1+REV","CHOR2+REV"
#ifdef FX_PS1
,"PS1"
#endif
};
const char *const fx_del_names[FX_DEL_COUNT]={"DELAY","CRUSH 1","CRUSH 2","CRU1+DEL","CRU2+DEL"
#ifdef FX_OCTAVE_POLISH
 ,"PING PONG","SHIMMER 1","SHIMMER 2"
#ifdef FX_CLOUD
 ,"CLOUD"
#endif
#elif defined(FX_NEW_DELAYS)
 ,"PING PONG","SHIMMER"
#endif
};
const u32 fx_rev_order[FX_REV_COUNT]={
#ifdef FX_PS1
7,
#endif
4,3,0,1,2,5,6},fx_del_order[FX_DEL_COUNT]={
#ifdef FX_CLOUD
8,7,6,5,
#elif defined(FX_OCTAVE_POLISH)
7,6,5,
#elif defined(FX_NEW_DELAYS)
6,5,
#endif
2,1,0,3,4};
#endif
static u32 loaded,back_owned,held,track_pending,track_start,track_used,flush_track;
static int motion;
#ifdef FX_CLOUD_REPAIR
/* Une rotation modifiee conserve son champ. Apres release FUNC, jeter les
 * deltas residuels jusqu a120ms de silence encodeur, sans toucher Window. */
static u32 cloud_owned,cloud_field,cloud_tick;
#endif
u32 fx_selected(void){u32 p=N(0x400cf866)();return p?N(0x40012412)(p+48):6;}
void fx_redraw(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
static u32 file(u32 write,u8*b){u32 h[4]={0},ok=0;u8 extra;if(N(0x4007bc5e)("/FxMix.cfg",write?"w":"r",h))return 0;
 if(write){if(!N(0x4007bb76)(h,0,60)&&N(0x4007bb0a)(b,60,h)==60&&!N(0x4007e2f6)(h))ok=1;}
 else if(N(0x4007baaa)(b,60,h)==60&&!N(0x4007baaa)(&extra,1,h))ok=1;
 if(N(0x4007bc1c)(h))ok=0;return ok;}
#ifdef FX_CLOUD
/* Fichier separe : format FxMix01 historique strictement conserve. */
static void cloud_settings(void){
 static u32 once;u32 h[4]={0};u8 b[10],extra;
 if(!once){once=1;
  if(!N(0x4007bc5e)("/Cloud.cfg","r",h)){
   u32 ok=N(0x4007baaa)(b,10,h)==10&&!N(0x4007baaa)(&extra,1,h);
   if(N(0x4007bc1c)(h))ok=0;
   if(ok&&!fx_dirty&&b[0]==67&&b[1]==76&&b[2]==48&&b[3]==49&&b[4]<128&&b[5]<25&&b[6]==(u8)~b[4]&&b[7]==(u8)~b[5]&&b[8]==165&&b[9]==90){fx_cloud_density=b[4];fx_cloud_pitch=b[5];}
  }
 }
 if(fx_dirty&&!N(0x4007faf4)(2)&&!fx_menu_open){
  u8 out[10]={67,76,48,49,fx_cloud_density,fx_cloud_pitch,(u8)~fx_cloud_density,(u8)~fx_cloud_pitch,165,90};
  if(!N(0x4007bc5e)("/Cloud.cfg","w",h)){
   if(!N(0x4007bb76)(h,0,10))N(0x4007bb0a)(out,10,h);
   N(0x4007e2f6)(h);N(0x4007bc1c)(h);
  }
 }
}
#endif
void fx_service(void){
 if(*(volatile u32*)0x40a7883c==1||!N(0x400d0a10)())return;
#ifdef FX_LEAN_FX
 /* Lire le vieux fichier d abord : FxMix conserve la priorite de selection. */
 cr_service();
#endif
#ifdef FX_CLOUD
 cloud_settings();
#endif
 u8 b[60]={70,88,48,49};
 if(!loaded){loaded=1;if(file(0,b)){u32 ok=b[0]==70&&b[1]==88&&b[2]==48&&b[3]==49&&b[58]==165&&b[59]==90&&b[4]<FX_REV_COUNT&&b[22]<
#if defined(FX_PS1)&&!defined(FX_CLOUD)
9
#else
FX_DEL_COUNT
#endif
&&b[24]>=2&&b[24]<=16;
  for(u32 i=0;i<27;i++)if(b[4+i]>127||b[31+i]!=(u8)~b[4+i])ok=0;
  if(ok&&!fx_dirty){
#ifdef FX_LEAN_FX
u32 prior_rev=b[4],prior_del=b[22];b[4]=(u8)fx_clean_rev(b[4]);b[22]=(u8)fx_clean_del(b[22]);fx_dirty=b[4]!=prior_rev||b[22]!=prior_del;
#endif
ch_mode=b[4];fx_speed=b[5];fx_depth=b[6];fx_crackle=b[7];fx_warble=b[8];fx_wspeed=b[9];cr_mode=b[22];
#if defined(FX_PS1)&&!defined(FX_CLOUD)
/* Retirer CLOUD sans perdre les autres preferences deja sauvegardees. */
if(cr_mode==8)cr_mode=0;
#endif
cr_rate=b[23];cr_bits=b[24];for(u32 t=0;t<6;t++){fx_aux_ch[t]=b[10+t];fx_aux_vi[t]=b[16+t];cr_send[t]=b[25+t];}}
 }}
 if(fx_dirty&&!N(0x4007faf4)(2)&&!fx_menu_open){b[4]=ch_mode;b[5]=fx_speed;b[6]=fx_depth;b[7]=fx_crackle;b[8]=fx_warble;b[9]=fx_wspeed;b[22]=cr_mode;b[23]=cr_rate;b[24]=cr_bits;
  for(u32 t=0;t<6;t++){b[10+t]=fx_aux_ch[t];b[16+t]=fx_aux_vi[t];b[25+t]=cr_send[t];}for(u32 i=0;i<27;i++)b[31+i]=~b[4+i];b[58]=165;b[59]=90;if(file(1,b))fx_dirty=0;
 }
}
void fx_commit(void){if(!fx_menu_open)return;u32 m=(fx_menu_slot?fx_del_order:fx_rev_order)[fx_menu_cursor];
 if(fx_menu_slot)cr_mode=m;else ch_mode=m;fx_dirty=1;fx_menu_open=0;motion=0;fx_notice((fx_menu_slot?fx_del_names:fx_rev_names)[m]);fx_redraw();}
u32 fx_query(u32 key){if(fx_force_active){
#ifdef FX_SETTINGS_SHORTCUTS
if(key==13)return 0;
#endif
if(key==1)return fx_force_func;if(key==2)return fx_force_track;}if(key==1&&fx_tap_force)return 1;return fx_query_original(key);}
static u32 native(u32 view,const u32*e,u32 knob,u32 func,u32 track){u32 copy[6];for(u32 i=0;i<6;i++)copy[i]=e[i];copy[3]=knob;
 fx_force_func=func;fx_force_track=track;fx_force_active=1;u32 ret=fx_native_encoder(view,copy);fx_force_active=0;
#ifdef FX_CLOUD_REPAIR
 if(cr_mode==8&&(knob==8||knob==15))fx_show(knob==8?14:func?13:12);
#endif
#ifdef FX_DELAY_REPAIR
 /* Le retour natif0 signifie parfois edition reussie. La route modifiee reste
  * proprietaire : ne jamais retomber sur le handler crusher historique. */
 (void)ret;return 1;
#else
 return ret;
#endif
}
/* Champs popup :0 Rate,1 Bits,2crushsend,3speed,4depth,5chorussend,
 *6crackle,7warble,8warblespeed,9vinylsend. */
void fx_parameter(u32 field,int delta){u32 lane=fx_selected(),*p=0,lo=0,hi=127;
 switch(field){case 0:p=(u32*)&cr_rate;break;case 1:p=(u32*)&cr_bits;lo=2;hi=16;break;case 2:if(lane<6)p=(u32*)&cr_send[lane];break;case 3:p=&fx_speed;break;case 4:p=&fx_depth;break;case 5:if(lane<6)p=&fx_aux_ch[lane];break;case 6:p=&fx_crackle;break;case 7:p=&fx_warble;break;case 8:p=&fx_wspeed;break;case 9:if(lane<6)p=&fx_aux_vi[lane];break;
#ifdef FX_CLOUD
 case 10:p=&fx_cloud_density;break;case 11:p=&fx_cloud_pitch;hi=24;break;
#endif
 }
 if(!p)return;int v=(int)*p+delta;if(v<(int)lo)v=lo;if(v>(int)hi)v=hi;*p=v;fx_dirty=1;fx_show(field);
}
u32 fx_encoder(u32 view,const u32*e){
#ifdef FX_LEAN_FX
 u32 clean_rev=fx_clean_rev(ch_mode),clean_del=fx_clean_del(cr_mode);
 if(clean_rev!=ch_mode||clean_del!=cr_mode){ch_mode=clean_rev;cr_mode=clean_del;fx_dirty=1;}
#endif
#ifdef FX_CPU_OPT
 if(e)fx_diag_cancel();
#endif
#ifdef FX_SETTINGS_SHORTCUTS
 /* SETTINGS reserve seulement Tone/Feedback combines ; noter l accord avant
  * le relais natif pour que sa release n ouvre pas CONFIG. */
 if(e&&e[0]==0x400fbebc&&!menu&&!fx_menu_open&&N(0x4007faf4)(13)&&!N(0x4007faf4)(1)&&!N(0x4007faf4)(2)&&!N(0x4007faf4)(8)&&
    ((e[3]==14&&ch_mode>=4&&ch_mode<FX_REV_COUNT)||(e[3]==15&&cr_mode>=3&&cr_mode<FX_DEL_COUNT))){
  extern volatile u32 fx_wf_api[];if(fx_wf_api[5])*(volatile u32*)fx_wf_api[5]=1;
#ifdef FX_OVERLAY_MENU
  /* Le handler stock peut retourner0 apres l edition. Ce resultat ne doit
   * jamais relancer le routeur non modifie et produire Size/Time une seconde fois. */
  native(view,e,e[3],1,0);return 1;
#else
  return native(view,e,e[3],1,0);
#endif
 }
#endif
 if(!e||e[0]!=0x400fbebc||menu||N(0x4007faf4)(13)||N(0x4007faf4)(8))return 0;
 u32 knob=e[3];if(knob!=8&&knob!=9&&knob!=14&&knob!=15){if(track_pending)track_used=1;return 0;}
 u32 func=!!N(0x4007faf4)(1),track=!!N(0x4007faf4)(2);
 if(track_pending)track=1;
#ifdef FX_CLOUD_REPAIR
 if(cr_mode==8&&knob==15&&cloud_owned){
  u32 now=*(volatile u32*)0xfc07000c;
  if(now-cloud_tick>16220160u)cloud_owned=0;
  else if(!func){cloud_tick=now;return 1;}
 }
#endif
 if((knob==14||knob==15)&&track&&!func){int delta=(int)N(0x4006f73a)(e,1,1);
  u32 slot=knob==15,n=slot?FX_DEL_MENU_COUNT:FX_REV_MENU_COUNT,current=slot?cr_mode:ch_mode;const u32*order=slot?fx_del_order:fx_rev_order;
  if(!fx_menu_open||fx_menu_slot!=slot){fx_menu_open=1;fx_menu_slot=slot;fx_menu_cursor=
#ifdef FX_LEAN_FX
0;
#else
slot?FX_DEL_COUNT-3:FX_REV_COUNT-5;
#endif
for(u32 i=0;i<n;i++)if(order[i]==current)fx_menu_cursor=i;motion=0;}
  if(delta){int sign=delta>0?1:-1;if(motion*sign<0)motion=0;motion+=sign;if(motion>=2||motion<=-2){motion=0;if(sign>0&&fx_menu_cursor+1<n)fx_menu_cursor++;if(sign<0&&fx_menu_cursor)fx_menu_cursor--;}}
  fx_redraw();return 1;
 }
 if(knob!=8&&knob!=9&&knob!=14&&knob!=15)return 0;
 if(track_pending)track_used=1;
 if(fx_menu_open)return 1;
 if(knob==15){
#ifdef FX_CLOUD
  if(cr_mode==8&&func){
#ifdef FX_CLOUD_REPAIR
   if(!cloud_owned){cloud_owned=1;cloud_field=track?11:10;}
   cloud_tick=*(volatile u32*)0xfc07000c;
   int delta=(int)N(0x4006f73a)(e,1,1);if(delta>1)delta=1;if(delta< -1)delta=-1;
   fx_parameter(cloud_field,delta);
#else
   fx_parameter(track?11:10,(int)N(0x4006f73a)(e,1,1));
#endif
   return 1;
  }
#endif
#ifdef FX_NEW_DELAYS
  if(FX_SPECIAL_DELAY(cr_mode))return native(view,e,15,func,0);
#endif
#ifndef FX_LEAN_FX
  if(cr_mode>=3){if(!func)return native(view,e,15,0,0);fx_parameter(track?1:0,(int)N(0x4006f73a)(e,1,1));return 1;}
#endif
  if(cr_mode){fx_parameter(func?1:0,(int)N(0x4006f73a)(e,1,1));return 1;}
  return native(view,e,15,func,track);
 }
#ifdef FX_LEAN_FX
 if(knob==8)return native(view,e,8,func,track);
#else
 if(knob==8){
#ifdef FX_NEW_DELAYS
 if(cr_mode>=3&&cr_mode<=4&&func){
#else
 if(cr_mode>=3&&func){
#endif
if(track)return native(view,e,15,1,0);fx_parameter(2,(int)N(0x4006f73a)(e,1,1));return 1;}return native(view,e,8,func,track);}
#endif
 if(knob==14){
  if(!ch_mode)return native(view,e,14,func,track);
#ifdef FX_PS1
  if(ch_mode==7)return native(view,e,14,func,0);
#endif
  if(ch_mode==1||ch_mode==2){fx_parameter(func?4:3,(int)N(0x4006f73a)(e,1,1));return 1;}
  if(ch_mode==3){fx_parameter(!func?6:track?8:7,(int)N(0x4006f73a)(e,1,1));return 1;}
#ifdef FX_LEAN_FX
  return native(view,e,14,func,0);
#else
  if(!func)return native(view,e,14,0,0);
  fx_parameter(ch_mode==4?(track?7:6):(track?4:3),(int)N(0x4006f73a)(e,1,1));return 1;
#endif
 }
#ifndef FX_LEAN_FX
 if(knob==9&&func&&ch_mode>=4
#ifdef FX_PS1
 &&ch_mode<=6
#endif
 ){fx_parameter(ch_mode==4?(track?8:9):5,(int)N(0x4006f73a)(e,1,1));return 1;}
#endif
 return native(view,e,9,func,track);
}
/* Appui FUNC puis TRACK : le tap reste stock ; le maintien appartient aux FX. */
u32 fx_key(u32*e){if(!e)return 0;
#ifdef FX_CPU_OPT
 fx_diag_gesture(e);
#endif
u32 code=e[3],flags=e[4],down=flags&1,fresh=down&&!(flags&0x28),was=held;
 if(code==1){
#ifdef FX_CLOUD_REPAIR
  if(fresh)cloud_owned=0;
#endif
 if(down)held|=1;else held&=~1u;}
 if(code==2){if(down)held|=2;else held&=~2u;}
 if(code==12&&back_owned){if(!down)back_owned=0;return 1;}
 if(fx_menu_open&&code==12&&fresh){fx_menu_open=0;motion=0;back_owned=1;fx_redraw();return 1;}
 if(code==2){
  if(fresh&&(was&1)&&!(was&2)){track_pending=1;track_used=0;track_start=*(volatile u32*)0xfc07000c;return 1;}
  if(track_pending){
   if(down)return 1;track_pending=0;
   if(!track_used&&*(volatile u32*)0xfc07000c-track_start<40550400u){e[4]=3;held|=2;fx_tap_force=1;flush_track=1;return 0;}
   return 1;
  }
  if(!down&&fx_menu_open)fx_commit();
 }
 return 0;
}
u32 fx_draw(u32 view,u32 canvas){
 u32 result=fx_previous_draw(view,canvas);if(flush_track){u32 e[6]={0,0,0,2,16,0};fx_native_keys(e);bl_physical&=~1u;held&=~2u;flush_track=0;}fx_tap_force=0;fx_service();
 if(!fx_menu_open)return result;

#ifdef FX_OVERLAY_MENU

 /* Fenetre opaque par-dessus la vue precedente, trois choix et marge visible. */
 N(0x40070efc)(canvas,12,4,119,57,0xffffffffu);
 N(0x40070efc)(canvas,10,6,117,59,0);
 N(0x40070c4e)(canvas,10,6,117,59,0xffffffffu);
 N(0x40071a04)(canvas,0x40ea14cc,17,48,0x10,"%s",fx_menu_slot?"DELAY FX":"REVERB FX");
 N(0x40070efc)(canvas,12,44,115,44,0xffffffffu);
 u32 n=fx_menu_slot?FX_DEL_MENU_COUNT:FX_REV_MENU_COUNT,top=fx_menu_cursor?fx_menu_cursor-1:0;if(top+3>n)top=n-3;
 for(u32 i=top;i<top+3&&i<n;i++){u32 y=33-12*(i-top),mode=(fx_menu_slot?fx_del_order:fx_rev_order)[i];
  N(0x40071a04)(canvas,0x40ea14cc,18,y,0x10,"%s",(fx_menu_slot?fx_del_names:fx_rev_names)[mode]);
  if(i==fx_menu_cursor)N(0x40070f6e)(canvas,14,y-1,112,y+10,0xffffffffu);
 }
 if(top)N(0x40071a04)(canvas,0x40ea14cc,108,33,0x10,"%s","^");
 if(top+3<n)N(0x40071a04)(canvas,0x40ea14cc,108,9,0x10,"%s","v");
#else
 N(0x40070efc)(canvas,0,0,127,63,0);N(0x40070c4e)(canvas,0,0,127,63,0xffffffffu);N(0x40071a04)(canvas,0x40ea14cc,3,53,0x10,"%s",fx_menu_slot?"DELAY FX":"REVERB FX");
 u32 n=fx_menu_slot?FX_DEL_MENU_COUNT:FX_REV_MENU_COUNT,top=fx_menu_cursor>2?fx_menu_cursor-2:0;if(top+5>n)top=n-5;
 for(u32 i=top;i<top+5&&i<n;i++){u32 y=41-10*(i-top),mode=(fx_menu_slot?fx_del_order:fx_rev_order)[i];N(0x40071a04)(canvas,0x40ea14cc,8,y,0x10,"%s",(fx_menu_slot?fx_del_names:fx_rev_names)[mode]);if(i==fx_menu_cursor)N(0x40070c4e)(canvas,3,y-1,124,y+9,0xffffffffu);}
#endif
 return 1;
}
