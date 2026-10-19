/* Test130 : overrides de filtre Wizard par piste, sans modifier les sons du pool.
 * Aucun getter UI dans IRQ : seules les valeurs capturees par le thread UI.
 * API : encodeur precedent, clavier precedent, dessin precedent, mm_params,
 * set_held, mod_used. Le menu de choix des pads reste volontairement en RAM.
 */
typedef unsigned int u32;
typedef signed int i32;
typedef unsigned short u16;
typedef unsigned char u8;
volatile u32 wf_api[6] __attribute__((section(".data")))={0};
volatile u32 wf_stock __attribute__((section(".data")))=0;
static volatile u32 enabled[6] __attribute__((section(".data")))={0};
static const volatile u16 *base[6] __attribute__((section(".data")))={0};
static u16 prior[6][2] __attribute__((section(".data")))={{0}};
static u32 prior_enabled[6] __attribute__((section(".data")))={0};
static volatile u16 target[6][2] __attribute__((section(".data")))={{0}};
static u32 gesture __attribute__((section(".data")))=0;
static u32 menu,editing,settings,menu_used;
static u32 valid(const u16 *p){return p&&((p[9]>>8)&255)==6;}
static u32 held(u32 key){return ((u32 (*)(u32))0x4007faf4)(key);}
static void repaint(void){u32 app=*(volatile u32 *)0x40fe4178;if(app)((void (*)(u32))0x40076bee)(app+64);}
u32 wf_menu_row(void){return 0;}
u32 wf_menu_edit(void){return editing;}
void wf_before(const u32 *event){
 gesture=0;
 if(!event||event[0]!=0x400fbebc||(event[3]!=6&&event[3]!=7))return;
 if(held(2)&&held(5)&&!held(1)&&!held(8))gesture=event[3]==6?1:2;
 for(u32 lane=0;lane<6;lane++){
  const u16 *p=((const u16 *(*)(u32))wf_api[3])(lane);
  if(base[lane]!=p||!valid(p))enabled[lane]=0;
  base[lane]=p;
  prior_enabled[lane]=enabled[lane];
  if(p){prior[lane][0]=p[13];prior[lane][1]=p[14];}
 }
}
void wf_after(const u32 *event){
 if(!event||event[0]!=0x400fbebc||(event[3]!=6&&event[3]!=7))return;
 for(u32 lane=0;lane<6;lane++){
  const volatile u16 *p=base[lane];
  if(!valid((const u16 *)p)){enabled[lane]=0;continue;}
  for(u32 field=0;field<2;field++){
   u32 bit=1u<<field;
   /* Seules les pistes reellement modifiees sont incluses : masque natif conserve. */
   u32 active=(prior_enabled[lane]&bit)||((gesture&bit)&&p[13+field]!=prior[lane][field]);
   if(active){target[lane][field]=p[13+field];enabled[lane]|=bit;}
  }
 }
 gesture=0;
}
u32 wf_value(const u16 *frame,u32 lane,u32 field){
 i32 value=(signed short)frame[13+field];
 if(lane<6&&field<2&&(enabled[lane]&(1u<<field))){
  const volatile u16 *p=base[lane];
  if(valid((const u16 *)p)&&p[13+field]==target[lane][field])value=target[lane][field];
  else enabled[lane]&=~(1u<<field); /* Changement de son/projet ou de parametre hors UI. */
 }
 return value<0?0:(u32)value;
}
/* Menu Pad Setup : SETTINGS + TRACK, DATA pour entrer, tourner pour choisir.
 * BACK ferme ; les autres gestes gardent leur delegation native.
 */
u32 wf_key(const u32 *event){
 if(!event)return 0;
 u32 code=event[3],flags=event[4];
 if(code==13){
  settings=(flags&1)!=0;
  if(wf_api[4])*(volatile u32 *)wf_api[4]=settings;
  /* Propager la release aux autres hooks (notamment mf_key) ; mod_used
   * empeche CONFIG d'apparaitre sans laisser SETTINGS colle ailleurs. */
  if(!settings&&menu_used){menu_used=0;if(wf_api[5])*(volatile u32 *)wf_api[5]=1;return 0;}
 }
 if(code==2&&(settings||menu_used)){
  if((flags&9)==1){menu=1;editing=0;menu_used=1;if(wf_api[5])*(volatile u32 *)wf_api[5]=1;repaint();}
  return 1;
 }
 if(!menu)return 0;
 if(code==12){if((flags&9)==1){menu=0;editing=0;repaint();}return 1;}
 if(code==32){if(flags&16){editing=!editing;repaint();}return 1;}
 return 0;
}
u32 wf_menu_encoder(const u32 *event){
 if(!menu||!event||event[0]!=0x400fbebc)return 0;
 if(event[3]!=1)return 1;
 if(editing){i32 delta=((i32 (*)(const u32 *,u32,u32))0x4006f73a)(event,1,1);if(delta)wf_stock=delta>0;repaint();}
 return 1;
}
extern void wf_menu_draw(u32,u32);
u32 wf_draw(u32 view,u32 canvas){if(!menu)return 0;wf_menu_draw(view,canvas);return 1;}
void wf_menu_value(u32 self,u32 item,u32 canvas,u32 x,u32 y){
 (void)self;(void)item;
 ((void (*)(u32,u32,u32,u32,u32,const char *,...))0x40071a04)(canvas,0x40ea14cc,x+24,y,4,"%s",wf_stock?"Stock":"Silent");
 if(editing)((void (*)(u32,u32,u32,u32,u32,u32))0x40070efc)(canvas,x-13,y-2,x+25,y+10,0xffffffffu);
}
