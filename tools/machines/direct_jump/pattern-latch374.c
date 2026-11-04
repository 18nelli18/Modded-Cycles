/* Verrou de selection natif, UI seulement : aucun etat de touche global force.
 * La seconde release PATTERN est absorbee APRES le suivi physique du controleur.
 * Le champ natif held du selecteur garde sa vue ouverte, sans minuterie ajoutee. */
typedef unsigned int u32;
typedef unsigned char u8;
extern u32 pl_old_key(u32,const u32*);
extern u32 pl_old_popup_key(u32,const u32*);
extern void pl_old_popup_frame(u32);
#define N(a) ((u32(*)())(a))
#define WINDOW 47308800u
volatile u32 pl_latched;
static u32 pressed,clean,armed,started,last,owned;
static u32 selector;
static u32 trace;
static u32 modified(void){return N(0x4007faf4)(1)||N(0x4007faf4)(2)||N(0x4007faf4)(4)||N(0x4007faf4)(5)||N(0x4007faf4)(13);}
static u32 mode(void){return N(0x4006bb18)(N(0x400cf9a8)())&255;}
static void close_selection(u32 view){
 pl_latched=armed=pressed=clean=0;
 *(volatile u8*)(view+0x90)=0;*(volatile u8*)(view+0x7c)=0;
 N(0x4006bb22)(N(0x400cf9a8)(),0);
 N(0x4002063c)(view);
 N(0x40076082)(view);
}
u32 pl_key(u32 view,const u32*e){
 if(!e)return pl_old_key(view,e);
 selector=view;
 u32 code=e[3],flags=e[4],down=flags&1,fresh=down&&!(flags&0x28);
 trace=(code<<8)|(flags&255);
 u32 now=*(volatile u32*)0xfc07000c;
 if(owned==code){if(!down)owned=0;return 1;}
 if(pl_latched&&!mode()){
  pl_latched=0;*(volatile u8*)(view+0x90)=0;
 }
 if(pl_latched&&(code==3||code==12)){
  if(fresh){close_selection(view);owned=code;return 1;}
  if(code==3)return 1;
 }
 if(code!=3){if(fresh)armed=clean=0;return pl_old_key(view,e);}
 if(down&&(flags&0x28)){armed=clean=0;}
 if(fresh&&!pressed){
  pressed=1;started=now;clean=!modified();
  u32 latch=clean&&armed&&now-last<=WINDOW&&mode();armed=0;
  /* Le press natif ferme la popup precedente et pose view.held=1.
   * Les trigs/chains utilisent ensuite le selecteur stock, sans faux GPIO. */
  u32 result=pl_old_key(view,e);
  if(latch&&mode()&&*(volatile u8*)(view+0x90))pl_latched=1;
  return result;
 }
 if(!down&&pressed){
  pressed=0;armed=clean&&now-started<=WINDOW;last=now;clean=0;
 }
 return pl_old_key(view,e);
}
u32 pl_popup_key(u32 popup,const u32*e){
 if(e){
  u32 code=e[3],flags=e[4],fresh=(flags&1)&&!(flags&0x28);
  trace=((code|128)<<8)|(flags&255);
  u32 now=*(volatile u32*)0xfc07000c;
  if((flags&1)&&(flags&0x28))armed=clean=0;
  if(pl_latched&&code==1)return 1;
  if(pl_latched&&selector&&(code==3||code==12||(code>=16&&code<=31))){
   pl_key(selector,e);return 1;
  }
  /* La popup recoit le second press AVANT le selecteur sous-jacent.
   * Armer ici evite que sa fermeture native annule le mode trop tot. */
  if(code==3&&fresh&&selector&&armed&&now-last<=WINDOW&&!modified()&&mode()){
   armed=clean=pressed=0;pl_latched=1;owned=3;
   *(volatile u8*)(selector+0x90)=1;*(volatile u8*)(selector+0x7c)=1;
   N(0x40076082)(selector);return 1;
  }
  if(fresh)armed=clean=0;
 }
 return pl_old_popup_key(popup,e);
}
void pl_popup_frame(u32 popup){
 if(pl_latched&&mode()){
  /* +0x60 est le compte a rebours du vrai TimedPopup natif.
   * Garder son traitement de frame, mais suspendre ce seul compteur. */
  volatile u32*count=(volatile u32*)(popup+0x60);u32 saved=*count;
  *count=0;pl_old_popup_frame(popup);*count=saved;return;
 }
 pl_old_popup_frame(popup);
}
void pl_snapshot(u8*d){
 d[0]='P';d[1]='L';d[2]=pl_latched;d[3]=pressed;d[4]=armed;d[5]=mode();
 d[6]=selector?*(volatile u8*)(selector+0x90):0;
 d[7]=selector?*(volatile u8*)(selector+0x7c):0;
 d[8]=trace>>8;d[9]=trace;
}
