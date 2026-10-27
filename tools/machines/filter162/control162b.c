/* Controle UI global par piste, aucune API UI dans le rendu audio. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#ifdef UI_IDLE210
extern u32 fc_input_quiet(void);
#define UI_QUIET() fc_input_quiet()
#else
#define UI_QUIET() 1
#endif

extern u32 sx_track(void),fc_native_draw(u32,u32);extern void fc_lohi_low(s32*,u32);extern void fc_low(s32*,u32),fc_high(s32*,u32),fc_band(s32*,u32);extern const unsigned short fc_native_table[128];
extern volatile u32 fc_track_used,menu;extern const unsigned short *fc_params(u32);
volatile u32 fc_type[6];static u32 open,cursor,lane,dirty,loaded,motion;
#ifdef FILTER_DEFAULTS208
#define EXTRA __attribute__((section(".fcextra")))
static u32 changed_before_load;
static void EXTRA fc_load_types(void);
u32 EXTRA fc_get_type_real(u32 t){fc_load_types();return t<6?fc_type[t]:0;}
void EXTRA fc_set_type_real(u32 t,u32 mode){if(t>=6||mode>3)return;fc_type[t]=mode;changed_before_load|=1u<<t;dirty=1;if(open&&lane==t)open=0;}
void EXTRA fc_reset_track_real(u32 t){
 if(t>=6)return;fc_set_type_real(t,0);u32 root=*(volatile u32*)0x40fe4228;if(!root)return;
 u32 obj=N(0x40009c1a)(root+116,t);if(!obj)return;u32 vt=*(const u32*)obj;u8*raw=vt?(u8*)N(*(const u32*)(vt+40))(obj):0;
 if(!raw||raw[38]==6||raw[38]==17)return;
 u32 records[4]={24,0x7f000000u,25,0},pair[2]={(u32)records,(u32)(records+4)};N(0x4001416c)(obj,pair);
}
/* Seul le chemin natif de son neuf est intercepte. Les lecteurs de fichiers
 * gardent leur initialisation generique ; charger un son ne reinitialise rien. */
u32 EXTRA fc_new_sound(u8*raw,u32 machine){
 u32 result=N(0x400618f2)(raw,machine),root=*(volatile u32*)0x40fe4228;
 if(raw&&raw[38]!=6&&raw[38]!=17){*(unsigned short*)(raw+68)=0x7f00;*(unsigned short*)(raw+70)=0;}
 if(root)for(u32 t=0;t<6;t++){u32 obj=N(0x40009c1a)(root+116,t);if(!obj)continue;u32 vt=*(const u32*)obj;if(vt&&N(*(const u32*)(vt+40))(obj)==(u32)raw){fc_reset_track_real(t);break;}}
 return result;
}
#endif
static const char*names[4]={"HIGH","LOW","BAND","LO/HI"};static const u8 order[4]={1,0,2,3};
static void redraw(void){u32 a=*(volatile u32*)0x40fe4178;if(a)N(0x40076bee)(a+64);}
#ifdef FILTER_KEYS202
/* SETTINGS d'abord : reserver MACHINES avant que le natif ouvre sa vue.
 * La release reste reservee meme si SETTINGS a deja ete relache. */
static u32 machine_owned;
static void fc_settings_used(void){extern volatile u32 fc_wf_api[];if(fc_wf_api[5])*(volatile u32*)fc_wf_api[5]=1;}
u32 fc_key_real(const u32*e){
#ifdef FILTER_NATIVE_KEYS203
 if(!e||e[0]!=0x400fc20c)return 0;
#else
 if(!e||e[0]!=0x400fbebc)return 0;
#endif
 u32 code=e[3],flags=e[4];
 if(code==13&&!(flags&1)&&machine_owned){fc_settings_used();return 0;}
 if(code!=5)return 0;
 if(machine_owned){if(!(flags&1))machine_owned=0;return 1;}
 if((flags&0x29)!=1||menu||!N(0x4007faf4)(13)||N(0x4007faf4)(1)||N(0x4007faf4)(2)||N(0x4007faf4)(8))return 0;
 u32 t=sx_track();if(t>=6)return 0;const unsigned short*p=fc_params(t);if(!p||(p[9]>>8)==6||(p[9]>>8)==17)return 0;
 machine_owned=1;fc_settings_used();return 1;
}
#endif
u32 fc_turn_real(const u32*e){
#ifdef FILTER_GESTURE200
 if(!e||menu||e[0]!=0x400fbebc||e[3]!=6||!N(0x4007faf4)(13)||!N(0x4007faf4)(5)||N(0x4007faf4)(2)||N(0x4007faf4)(1)||N(0x4007faf4)(8))return 0;
#else
 if(!e||menu||e[0]!=0x400fbebc||e[3]!=6||!N(0x4007faf4)(2)||N(0x4007faf4)(1)||N(0x4007faf4)(8))return 0;
#endif
 u32 t=sx_track();if(t>=6)return 0;const unsigned short*p=fc_params(t);if(!p||(p[9]>>8)==6||(p[9]>>8)==17)return 0;
 s32 delta=(s32)N(0x4006f73a)(e,1,1);if(!open){open=1;lane=t;motion=0;cursor=1;for(u32 i=0;i<4;i++)if(order[i]==fc_type[t])cursor=i;}
#ifdef FILTER_GESTURE200
 /* Consommer SETTINGS comme les raccourcis Estus : aucun CONFIG au relachement. */
 extern volatile u32 fc_wf_api[];if(fc_wf_api[5])*(volatile u32*)fc_wf_api[5]=1;
#else
 fc_track_used=1;
#endif
 if(delta){s32 sign=delta>0?1:-1;s32 next=(s32)cursor+sign;if(next<0)next=0;if(next>3)next=3;cursor=(u32)next;}
 redraw();return 1;
}
u32 fc_draw_real(u32 view,u32 canvas){
 if(!open)return 0;fc_native_draw(view,canvas);
 N(0x40070efc)(canvas,12,4,119,57,0xffffffffu);N(0x40070efc)(canvas,10,6,117,59,0);N(0x40070c4e)(canvas,10,6,117,59,0xffffffffu);
 N(0x40071a04)(canvas,0x40ea14cc,17,48,0x10,"%s","FILTER");N(0x40070efc)(canvas,12,44,115,44,0xffffffffu);
 u32 top=cursor>1?cursor-1:0;if(top>1)top=1;
 for(u32 i=top;i<top+3;i++){u32 y=33-12*(i-top);N(0x40071a04)(canvas,0x40ea14cc,18,y,0x10,"%s",names[i]);if(i==cursor)N(0x40070f6e)(canvas,14,y-1,112,y+10,0xffffffffu);}
 return 1;
}
/* Le slot24 est la coupure partagee ; publication native du mot8.8. */
static void center(u32 t){
 u32 root=N(0x400cf866)();if(!root)return;
 u32 bank=N(0x4000eb9c)(root);if(!bank)return;
 u32 obj=N(0x40009c1a)(bank,t);if(!obj)return;
 u32 records[2]={24,0x40000000u};u32 pair[2]={(u32)records,(u32)(records+2)};
 N(0x4001416c)(obj,pair);
}
#ifdef FILTER_DEFAULTS208
static void EXTRA fc_load_types(void){u32 h[4]={0};u8 b[18],extra;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/Filter.cfg","r",h)){u32 ok=N(0x4007baaa)(b,18,h)==18&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);if(b[0]!='F'||b[1]!='C'||b[2]!=1||b[3]!=6||b[16]!=165||b[17]!=90)ok=0;for(u32 i=0;i<6;i++)if(b[4+i]>3||b[10+i]!=(u8)~b[4+i])ok=0;if(ok)for(u32 i=0;i<6;i++)if(!(changed_before_load&(1u<<i)))fc_type[i]=b[4+i];}}
}
#endif
void fc_frame_real(void){
#ifdef FILTER_GESTURE200
 if(open&&(!N(0x4007faf4)(13)||!N(0x4007faf4)(5))){
#else
 if(open&&!N(0x4007faf4)(2)){
#endif
 if(lane<6){if(order[cursor]==3&&fc_type[lane]!=3)center(lane);fc_type[lane]=order[cursor];dirty=1;}open=0;redraw();}
 u32 h[4]={0};u8 b[18],extra;
#ifdef FILTER_DEFAULTS208
 (void)extra;
 fc_load_types();
#else
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/Filter.cfg","r",h)){u32 ok=N(0x4007baaa)(b,18,h)==18&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);if(b[0]!='F'||b[1]!='C'||b[2]!=1||b[3]!=6||b[16]!=165||b[17]!=90)ok=0;for(u32 i=0;i<6;i++)if(b[4+i]>3||b[10+i]!=(u8)~b[4+i])ok=0;if(ok)for(u32 i=0;i<6;i++)fc_type[i]=b[4+i];}}
#endif
 if(dirty&&UI_QUIET()&&!open&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c){b[0]='F';b[1]='C';b[2]=1;b[3]=6;b[16]=165;b[17]=90;for(u32 i=0;i<6;i++){b[4+i]=fc_type[i];b[10+i]=~b[4+i];}if(!N(0x4007bc5e)("/Filter.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,18)&&N(0x4007bb0a)(b,18,h)==18&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)dirty=0;}}
}
void fc_filter(s32*out,u32 t){
 if(t>=6)return;u32 mode=fc_type[t];
 if(mode==0||mode>3){fc_low(out,t);return;}
 u32 f=((volatile u32*)0x401bbd60)[t],index=127;
 if(f){u32 lo=0,hi=127;while(lo<hi){u32 mid=(lo+hi)/2;if(fc_native_table[mid]<f)lo=mid+1;else hi=mid;}index=lo;}
 if(mode==3&&index==64)return;
 if(!f)((volatile u32*)0x401bbd60)[t]=fc_native_table[127];
 if(mode==1||(mode==3&&index>64))fc_high(out,t);else if(mode==2)fc_band(out,t);else fc_lohi_low(out,t);
 ((volatile u32*)0x401bbd60)[t]=f;
}
