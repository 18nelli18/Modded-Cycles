/* Ducking par declenchement : six sources, enveloppes bornees, aucun float.
 * Les gains portent sur les blocs mid/side avant gain, panoramique et envois. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 menu,row,sx_submenu;extern volatile u8 sx_masks[6];
extern u32 du_previous_key(const u32*),du_previous_encoder(const u32*),du_previous_draw(u32,u32),du_previous_note(u32*);
extern void du_previous_audio(void),du_previous_step(u32*);
extern u32 wf_menu_edit(void),sx_track(void);extern void du_root_draw(u32,u32),du_sub_draw(u32,u32);
extern u32 br_side,br_side_on;
volatile u8 du_config[6][5];
volatile u32 du_pending,du_enabled,du_page,du_row,du_edit;
static u32 owned_data,owned_back,initialized,working;
static u32 gain[6];
struct envelope{u32 level,stage,ticks,step;};static struct envelope env[6];
const u32 du_attack_ms[8]={0,2,5,10,20,40,80,160};
const u32 du_hold_ms[4]={0,20,60,120};
const u32 du_release_ms[16]={10,20,30,50,75,100,150,200,300,400,500,750,1000,1500,2000,3000};
struct {u32 n,cap,ref;char text[12];} du_title_track={8,8,0,"Chain T1"};
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
static u32 source(void){return sx_track();}
void du_refresh(void){u32 mask=0;for(u32 i=0;i<6;i++)if(du_config[i][0]&&du_config[i][1])mask|=1u<<i;du_enabled=mask;}
void du_reset(void){du_pending=0;for(u32 i=0;i<6;i++){env[i].level=env[i].stage=0;if(!initialized)gain[i]=65536;}initialized=1;du_refresh();}
/* Le constructeur SCRAMBLE precede la file temporelle : ne pas declencher ici.
 * Le filtre de notes est appele lors de l'echeance, avant le masque mute natif. */
void du_note(u32*e){if(e&&du_enabled&&e[0]==0&&e[1]==1&&e[2]<6&&e[3]!=0xffffffffu&&(e[3]!=1||(e[10]&1)))du_pending|=1u<<e[2];}
u32 du_note_filter(u32*e){u32 result=du_previous_note(e);du_note(e);return result;}
void du_voice_triggers(u32 mask){du_pending|=mask&du_enabled;}
static u32 blocks(u32 ms){return (ms*3+1)/2;}
static void release(struct envelope*e,u32 t){e->stage=3;e->ticks=blocks(du_release_ms[du_config[t][4]]);if(!e->ticks)e->ticks=1;e->step=(e->level+e->ticks-1)/e->ticks;}
static u32 advance(u32 t,u32 pulse){
 struct envelope*e=&env[t];u32 target=du_config[t][1]*4369;
 if(pulse){e->ticks=blocks(du_attack_ms[du_config[t][2]]);e->stage=e->ticks?1:2;e->step=e->ticks&&target>e->level?(target-e->level+e->ticks-1)/e->ticks:0;if(!e->ticks){e->level=target;e->ticks=blocks(du_hold_ms[du_config[t][3]]);}}
 if(e->stage==1){if(e->level<target){e->level+=e->step;if(e->level>target)e->level=target;}else e->level=target;if(e->ticks)--e->ticks;if(!e->ticks){e->level=target;e->stage=2;e->ticks=blocks(du_hold_ms[du_config[t][3]]);}}
 else if(e->stage==2){if(e->ticks)--e->ticks;else release(e,t);}
 else if(e->stage==3){e->level=e->level>e->step?e->level-e->step:0;if(e->ticks)--e->ticks;if(!e->ticks)e->level=e->stage=0;}
 return e->level;
}
static s32 multiply(s32 x,u32 g){return (s32)((u32)((x>>16)*(s32)g)+((((u32)x&65535)*g)>>16));}
void du_process(void){
 if(!du_enabled&&!working){du_pending=0;return;}if(!initialized)du_reset();
 u32 pending=du_pending;du_pending=0;u32 goals[6]={65536,65536,65536,65536,65536,65536};
 for(u32 src=0;src<6;src++)if(du_enabled&(1u<<src)){
  u32 amount=advance(src,pending&(1u<<src)),mask=du_config[src][0]&~(1u<<src),want=65536-amount;
  for(u32 dst=0;dst<6;dst++)if((mask&(1u<<dst))&&want<goals[dst])goals[dst]=want;
 }
 working=0;
 for(u32 t=0;t<6;t++){
  u32 before=gain[t],after=goals[t];if(after!=65536)working=1;
  if(before!=65536||after!=65536){
   s32 *mid=(s32*)(0x80001858+128*t),*side=br_side&&((u32*)br_side_on)[t]?(s32*)(br_side+128*t):0;
   s32 delta=(s32)after-(s32)before;
   for(u32 i=0;i<32;i++){u32 g=(u32)((s32)before+((delta*(s32)(i+1))>>5));mid[i]=multiply(mid[i],g);if(side)side[i]=multiply(side[i],g);}
  }gain[t]=after;
 }
}
void du_audio(void){du_previous_audio();du_process();}
u32 du_key(const u32*e){if(!e)return 0;u32 code=e[3],f=e[4];
 if(code==12&&owned_back){if(!(f&1))owned_back=0;return 1;}
 if(menu&&du_page){
  if(code==12){if((f&9)==1){if(du_edit)du_edit=0;else{du_page=0;row=7;}owned_back=1;repaint();}return 1;}
  if(code==32){if((f&9)==1)owned_data=1;if((f&16)&&owned_data){owned_data=0;if(du_row<5){u32 s=source(),dst=du_row+(du_row>=s);du_config[s][0]^=1u<<dst;du_refresh();}else du_edit=!du_edit;repaint();}return 1;}
 }else if(menu&&!sx_submenu&&row==7&&code==32){if((f&9)==1)owned_data=1;if((f&16)&&owned_data){owned_data=0;du_page=1;du_row=du_edit=0;repaint();}return 1;}
 u32 result=du_previous_key(e);if(!menu)du_page=du_edit=0;return result;
}
u32 du_encoder(const u32*e){if(!menu||!e||e[0]!=0x400fbebc)return du_previous_encoder(e);if(e[3]!=1)return 1;
 if(du_page){s32 d=(s32)N(0x4006f73a)(e,1,1);if(!d)return 1;if(!du_edit)du_row=(du_row+(d>0?1:8))%9;else{u32 s=source(),field=du_row-4,hi=field==2?7:field==3?3:15;s32 n=(s32)du_config[s][field]+d;if(n<0)n=0;if(n>(s32)hi)n=hi;du_config[s][field]=(u8)n;du_refresh();}repaint();return 1;}
 if(!sx_submenu&&!wf_menu_edit()){s32 d=(s32)N(0x4006f73a)(e,1,1);if(d){row=(row+(d>0?1:7))%8;repaint();}return 1;}
 return du_previous_encoder(e);
}
u32 du_draw(u32 view,u32 canvas){if(!menu){du_page=du_edit=0;return du_previous_draw(view,canvas);}if(du_page){du_title_track.text[7]='1'+source();du_sub_draw(view,canvas);}else if(!sx_submenu)du_root_draw(view,canvas);else return du_previous_draw(view,canvas);return 1;}
u32 du_menu_row(void){return du_row;}u32 du_menu_edit(void){return du_edit;}
void du_root_value(u32 a,u32 b,u32 canvas,u32 x,u32 y){(void)a;(void)b;(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);N(0x40071a04)(canvas,font,126,y,4,"%s","Sidechain");N(0x40072080)(font);}
static void value(u32 line,u32 canvas,u32 x,u32 y){(void)x;u32 font[2];N(0x40072260)(font,0x40140ab0);u32 s=source();const char*labels[9]={"Track","Track","Track","Track","Track","Depth","Atk","Hold","Rel"};
 N(0x40071a04)(canvas,font,65,y,0x10,"%s",labels[line]);
 if(line<5){u32 dst=line+(line>=s);N(0x40071a04)(canvas,font,109,y,4,"%u",dst+1);N(0x40070c4e)(canvas,119,y,126,y+7,0xffffffffu);if(du_config[s][0]&(1u<<dst))N(0x40070efc)(canvas,121,y+2,124,y+5,0xffffffffu);}
 else{u32 f=line-4,v=du_config[s][f];if(f==1)N(0x40071a04)(canvas,font,126,y,4,"%u%%",(v*100+7)/15);
 else{u32 ms=f==2?du_attack_ms[v]:f==3?du_hold_ms[v]:du_release_ms[v];if(ms>=1000){if(ms%1000)N(0x40071a04)(canvas,font,126,y,4,"%u.%us",ms/1000,(ms%1000)/100);else N(0x40071a04)(canvas,font,126,y,4,"%us",ms/1000);}else N(0x40071a04)(canvas,font,126,y,4,"%ums",ms);}}N(0x40072080)(font);}
#define VALUE(i) void du_value##i(u32 a,u32 b,u32 c,u32 x,u32 y){(void)a;(void)b;value(i,c,x,y);}
VALUE(0) VALUE(1) VALUE(2) VALUE(3) VALUE(4) VALUE(5) VALUE(6) VALUE(7) VALUE(8)
