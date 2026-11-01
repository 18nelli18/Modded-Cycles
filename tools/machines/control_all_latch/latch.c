/* Verrou UI seulement : aucune touche TRACK synthetique hors encodeur.
 * Deux taps propres de350ms maximum ; BACK simple conserve undo natif. */
typedef unsigned int u32;
#define N(a) ((u32(*)())(a))
extern u32 cal_old_key(u32,const u32*),cal_old_encoder(u32,const u32*),cal_old_held(u32);
extern void fx_notice(const char*);
extern volatile u32 menu;
volatile u32 cal_latched,cal_scope;
static u32 physical,clean,armed,last,started,second,owned;
static u32 bp,bc,ba,bl,bs,bo;
#define WINDOW 47308800u
u32 cal_held(u32 code){if(code==2&&cal_scope)return 1;return cal_old_held(code);}
static u32 modified(void){return cal_old_held(1)||cal_old_held(4)||cal_old_held(5)||cal_old_held(13);}
static u32 native_back(u32 view,const u32*e){
 u32 prior=cal_scope;cal_scope=cal_latched&&!menu&&!modified();
 u32 result=cal_old_key(view,e);cal_scope=prior;return result;
}
u32 cal_key(u32 view,const u32*e){
 if(!e)return cal_old_key(view,e);
 u32 code=e[3],flags=e[4],down=flags&1,fresh=down&&!(flags&0x28),now=*(volatile u32*)0xfc07000c;
 if(code==12){
  armed=clean=second=0;
  if(bo){if(!down)bo=bp=0;return 1;}
  if(down&&(flags&0x28))bc=ba=0;
  if(fresh&&!bp){
   bp=1;bs=now;bc=cal_latched&&!menu&&!modified();
   if(bc&&ba&&now-bl<=WINDOW){cal_latched=cal_scope=ba=0;bo=1;fx_notice("CTRL-ALL OFF");return 1;}
   ba=0;
  }
  if(!down&&bp){bp=0;ba=bc&&cal_latched&&!menu&&!modified()&&now-bs<=WINDOW;bl=now;bc=0;}
  return native_back(view,e);
 }
 if(fresh){ba=0;if(bp)bc=0;}
 if(code==2){
  if(owned){if(!down){owned=physical=0;}return 1;}
  if(down&&(flags&0x28)){clean=second=armed=0;}
  if(fresh&&!physical){
   physical=1;started=now;
   if(cal_latched){cal_latched=cal_scope=armed=0;owned=1;fx_notice("CTRL-ALL OFF");return 1;}
   clean=!menu&&!modified();second=clean&&armed&&now-last<=WINDOW;armed=0;
  }
  if(!down&&physical){
   physical=0;u32 toggle=clean&&now-started<=WINDOW&&second;
   armed=clean&&now-started<=WINDOW&&!second;last=now;clean=second=0;
   /* Toujours terminer la release native avant d afficher le verrou. */
   u32 result=cal_old_key(view,e);
   if(toggle){cal_latched=1;fx_notice("CTRL-ALL ON");}return result;
  }
 }else if(fresh){armed=clean=second=0;}
 return cal_old_key(view,e);
}
u32 cal_encoder(u32 view,const u32*e){
 if(physical)clean=second=0;armed=0;ba=bc=0;
 u32 prior=cal_scope;
 /* DATA1 et les selecteurs FX14/15 restent physiques. SETTINGS/MACHINES
  * gardent leurs raccourcis ; aucun verrou dans Mod Setup/Song. */
 cal_scope=cal_latched&&!menu&&e&&e[0]==0x400fbebc&&e[3]>=2&&e[3]<=13&&!cal_old_held(5)&&!cal_old_held(13);
 u32 result=cal_old_encoder(view,e);cal_scope=prior;return result;
}
