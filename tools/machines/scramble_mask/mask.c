/* Masques SCRAMBLE par piste, E/S uniquement UI arrete ; six slots audio.
 * Le constructeur de locks ne touche que l'evenement, jamais le son sauvegarde. */
typedef unsigned int u32;typedef int i32;typedef unsigned short u16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 menu,row,sc_result;
extern u32 sx_previous_key(const u32*),sx_previous_encoder(const u32*),sx_previous_draw(u32,u32),sx_previous_run(void);
extern u32 wf_menu_edit(void),sx_random(void);extern void sx_bounds(u32,i32*),sx_notice(const char*);
extern void sx_root_draw(u32,u32),sx_sub_draw(u32,u32);
volatile u8 sx_masks[6] __attribute__((section(".data")))={60,60,60,60,60,60};
volatile u32 sx_submenu,sx_subrow;static u32 loaded,dirty,back_owned,data_owned;
struct {u32 n,cap,ref;char text[4];} sx_track_string={2,2,0,"T1"};
/* Decay : slot18/CC80. Punch : slot15/CC66. Le mapping CC80 renvoie
 * le descripteur commun plutot que le descripteur propre a chaque moteur.
 * v65 ciblait Punch par erreur ; v66 resout explicitement le vrai Decay. */
#ifdef SX_DECAY_NATIVE
static const u32 slots[6]={10,18,11,12,13,14};
#elif defined(SX_DECAY_FIX)
static const u32 slots[6]={10,15,11,12,13,14};
#else
static const u32 slots[6]={10,18,11,12,13,14};
#endif
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
u32 sx_track(void){u32 p=N(0x400cf866)();u32 t=p?N(0x40012412)(p+48):0;return t<6?t:0;}
u32 sx_mask(u32 t){return t<6?sx_masks[t]&63:60;}
static u32 file(u32 write,u8 *b){u32 h[4]={0},ok=0;u8 extra;if(N(0x4007bc5e)("/Scramble.cfg",write?"w":"r",h))return 0;
 if(write){if(!N(0x4007bb76)(h,0,18)&&N(0x4007bb0a)(b,18,h)==18&&!N(0x4007e2f6)(h))ok=1;}
 else if(N(0x4007baaa)(b,18,h)==18&&!N(0x4007baaa)(&extra,1,h))ok=1;
 if(N(0x4007bc1c)(h))ok=0;return ok;}
static void service(void){if(*(volatile u32*)0x40a7883c==1||!N(0x400d0a10)())return;u8 b[18]={83,67,48,49,0,0,0,0,0,0,0,0,0,0,0,0,165,90};
 if(!loaded){loaded=1;if(file(0,b)){u32 good=b[0]==83&&b[1]==67&&b[2]==48&&b[3]==49&&b[16]==165&&b[17]==90;
  for(u32 i=0;i<6;i++)if(b[4+i]>63||b[10+i]!=(u8)~b[4+i])good=0;
  if(good)for(u32 i=0;i<6;i++)sx_masks[i]=b[4+i];}}
 if(dirty&&!sx_submenu){b[0]=83;b[1]=67;b[2]=48;b[3]=49;b[16]=165;b[17]=90;for(u32 i=0;i<6;i++){b[4+i]=sx_masks[i];b[10+i]=~b[4+i];}if(file(1,b))dirty=0;}}
u32 sx_key(const u32 *e){if(!e)return 0;u32 code=e[3],f=e[4];
 if(code==12&&back_owned){if(!(f&1))back_owned=0;return 1;}
 if(menu&&sx_submenu){
  if(code==12){if((f&9)==1){sx_submenu=0;back_owned=1;row=6;repaint();}return 1;}
  if(code==32){if((f&9)==1)data_owned=1;if((f&16)&&data_owned){data_owned=0;u32 t=sx_track();sx_masks[t]^=1u<<sx_subrow;dirty=1;repaint();}return 1;}
 }
 else if(menu&&row==6&&code==32){if((f&9)==1)data_owned=1;if((f&16)&&data_owned){data_owned=0;sx_submenu=1;sx_subrow=0;repaint();}return 1;}
 u32 result=sx_previous_key(e);if(!menu)sx_submenu=0;return result;}
u32 sx_encoder(const u32 *e){if(!menu||!e||e[0]!=0x400fbebc)return sx_previous_encoder(e);if(e[3]!=1)return 1;
 i32 d=(i32)N(0x4006f73a)(e,1,1);if(!d)return 1;
 if(sx_submenu){sx_subrow=(sx_subrow+(d>0?1:5))%6;repaint();return 1;}
 if(!wf_menu_edit()){row=(row+(d>0?1:6))%7;repaint();return 1;}
 if(row==6)return 1;return sx_previous_encoder(e);}
u32 sx_draw(u32 view,u32 canvas){service();if(!menu){sx_submenu=0;return sx_previous_draw(view,canvas);}if(sx_submenu){sx_track_string.text[1]='1'+sx_track();sx_sub_draw(view,canvas);}else sx_root_draw(view,canvas);return 1;}
u32 sx_menu_row(void){return sx_subrow;}u32 sx_menu_edit(void){return 0;}
void sx_root_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;N(0x40071a04)(canvas,0x40ea14cc,x+24,y,4,"%s",">");}
static void check(u32 bit,u32 canvas,u32 y){u32 on=sx_mask(sx_track())&(1u<<bit);N(0x40070c4e)(canvas,119,y,126,y+7,0xffffffffu);if(on){N(0x40070efc)(canvas,121,y+2,124,y+5,0xffffffffu);}}
#define VALUE(name,bit) void name(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;(void)x;check(bit,c,y);}
VALUE(sx_pitch_value,0) VALUE(sx_decay_value,1) VALUE(sx_color_value,2) VALUE(sx_shape_value,3) VALUE(sx_sweep_value,4) VALUE(sx_contour_value,5)
/* Construire et valider toutes les valeurs avant la premiere ecriture. */
static u32 plan(u32 machine,u32 mask,u32 *slot,u32 *value,u32 *cc,u32 lane,u32 live){u32 n=0;
 for(u32 i=0;i<6;i++){if(!(mask&(1u<<i))||(machine==6&&i>=2))continue;u32 desc=N(0x4005a692)(slots[i],machine);
#ifdef SX_DECAY_NATIVE
  if(i==1)desc=N(0x4005a8ce)(lane,machine,80);
#endif
  if(!desc)continue;i32 b[3];sx_bounds(desc,b);i32 lo=(b[0]+255)>>8,hi=b[1]>>8;if(lo<0||hi>127||hi<lo)continue;
  u32 c=N(0x4005a7f8)(desc);if(live&&(c>127||N(0x4005a8ce)(lane,machine,c)!=desc))continue;
  slot[n]=slots[i];value[n]=lo+(sx_random()&65535)%(u32)(hi-lo+1);cc[n]=c;n++;}return n;}
u32 sx_run(void){sc_result=0;u32 project=N(0x400cf866)();if(!project)return 0;u32 lane=N(0x40012412)(project+48);if(lane>5)return 0;u32 handle=project+212+68*lane;u32 vt=*(u32*)handle;if(!vt)return 0;
 u8 *sound=(u8*)N(*(u32*)(vt+40))(handle);if(!sound)return 0;u32 machine=sound[38];if(machine==17)return sx_previous_run();
 u32 s[6],v[6],c[6],n=plan(machine,sx_mask(lane),s,v,c,lane,1);for(u32 i=0;i<n;i++)N(0x4000f2a2)(project,c[i],v[i],lane,0);
 sc_result=!!n;sx_notice("SCRAMBLE");return !!n;}
void sx_step(u32 *e){if(!(e[10]&64))return;e[10]&=~64u;u8 *sound=(u8*)e[11];u32 *locks=(u32*)e[18];if(!sound||!locks||e[2]>5||locks[2]>33)return;
 u32 machine=sound[38],s[6],v[6],c[6],where[6],count=locks[2],needed=0,n=plan(machine,machine==17?60:sx_mask(e[2]),s,v,c,e[2],0);u8 *p=(u8*)locks+20;
 for(u32 i=0;i<n;i++){u32 j;for(j=0;j<count;j++)if(*(u16*)(p+8*j)==s[i])break;where[i]=j;if(j==count)needed++;}if(count+needed>33)return;
 for(u32 i=0;i<n;i++){u32 j=where[i];if(j==count){j=locks[2]++;*(u16*)(p+8*j)=s[i];*(u32*)(p+8*j+4)=0;}*(u16*)(p+8*j+2)=v[i]<<8;}}
void *memset(void*p,int v,u32 n){u8*d=p;while(n--)*d++=v;return p;}
void *memcpy(void*p,const void*q,u32 n){u8*d=p;const u8*s=q;while(n--)*d++=*s++;return p;}
