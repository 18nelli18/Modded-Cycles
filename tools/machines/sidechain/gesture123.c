/* Inversion des gestes UI : appui bref menu, maintien SCRAMBLE une fois.
 * Reutiliser les globals/API du controleur existant conserve les releases
 * SETTINGS et les gardes CONFIG. Aucun changement des chemins audio. */
typedef unsigned int u32;
extern volatile u32 wm_menu,wm_editing,wm_settings,wm_used,wm_owned,wm_pending,wm_api[9];
extern u32 wm_steps(void);
#define N(a) ((u32(*)())(a))
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
static void scramble(const u32*event){
 if(!wm_pending)return;wm_pending=0;
 if(wm_api[6]){u32 copy[6];for(u32 i=0;i<6;i++)copy[i]=event[i];
  u32 old=wm_api[4]?*(volatile u32*)wm_api[4]:0;
  if(wm_api[4])*(volatile u32*)wm_api[4]=1;
  copy[3]=2;copy[4]=1;N(wm_api[6])(copy);copy[4]=16;N(wm_api[6])(copy);
  if(wm_api[4])*(volatile u32*)wm_api[4]=old;
 }
}
static void tap(void){
 if(!wm_pending)return;wm_pending=0;
 /* Cette routine ne tire jamais le son de base :0 signifie aucun trig tenu. */
 if(wm_steps())return;
 wm_menu=1;wm_editing=0;repaint();
}
u32 wm_key(const u32*event){
 if(!event)return 0;u32 code=event[3],flags=event[4];
#ifdef WM_MACHINE_EXIT
 /* MACHINES ouvre une vue native. Ne pas garder le menu UI proprietaire
  * des encodeurs derriere : les wrappers sx/du nettoient leurs sous-pages
  * quand menu devient nul. L'evenement physique reste transmis intact. */
 if(code==5&&(flags&0x29)==1&&wm_menu){wm_menu=wm_editing=wm_pending=0;repaint();return 0;}
#endif
 if(code==13){
  if(!(flags&1))tap();
  wm_settings=(flags&1)!=0;
  if(wm_api[4])*(volatile u32*)wm_api[4]=wm_settings;
  if(!wm_settings&&wm_used){wm_used=0;if(wm_api[5])*(volatile u32*)wm_api[5]=1;return 0;}
 }
 if(code==2&&(wm_settings||wm_owned)){
  if((flags&9)==1
#ifdef WM_ONCE
    &&!wm_owned
#endif
  ){wm_owned=1;wm_pending=!wm_menu;wm_used=1;if(wm_api[5])*(volatile u32*)wm_api[5]=1;}
  if((flags&32)&&wm_pending)scramble(event);
  if(!(flags&1)){tap();wm_owned=0;}
  return 1;
 }
 if(!wm_menu)return 0;
 if(code==12){if((flags&9)==1){wm_menu=0;wm_editing=0;repaint();}return 1;}
 if(code==32){if(flags&16){wm_editing=!wm_editing;repaint();}return 1;}
 return 0;
}
