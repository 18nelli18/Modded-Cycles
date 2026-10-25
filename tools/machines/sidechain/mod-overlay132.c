/* Menu Mod au-dessus des vues natives ; edition des sons sans perdre la page.
 * Thread UI uniquement. Le timeout/repaint precede le mutex de dessin. */
typedef unsigned int u32;
extern volatile u32 mo_menu;
extern u32 mo_previous_encoder(u32,const u32*),mo_previous_key(const u32*);
extern u32 mo_previous_draw(u32,u32),mo_previous_stack(u32,u32),mo_menu_encoder(const u32*);
extern void mo_previous_frame(void);
#define N(a) ((u32(*)())(a))
#define PREVIEW_TICKS 135168000u
static u32 preview,stamp,owned_back,owned_data;
static u32 now(void){return *(volatile u32*)0xfc07000c;}
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
u32 mo_encoder(u32 view,const u32*e){
 if(!mo_menu||!e||e[0]!=0x400fbebc)return mo_previous_encoder(view,e);
 if(e[3]==1){preview=0;return mo_menu_encoder(e);}
 /* Les autres encodeurs gardent le trajet FX/MIDI/parametres natif complet.
  * Masquer seulement l'intercepteur de menu pendant cette delegation ; ne
  * jamais passer par ses dessinateurs pendant menu=0 (ils effacent les pages). */
 if(e[3]<2||e[3]>15)return 1;
 u32 saved=mo_menu;mo_menu=0;preview=1;stamp=now();
 mo_previous_encoder(view,e);mo_menu=saved;
 return 1;
}
u32 mo_key(const u32*e){
 if(!e)return mo_previous_key(e);u32 code=e[3],f=e[4];
 if(code==12&&owned_back){if(!(f&1))owned_back=0;return 1;}
 if(code==32&&owned_data){if(!(f&1))owned_data=0;return 1;}
 if(mo_menu&&preview&&(code==12||code==32)&&(f&0x29)==1){
  preview=0;if(code==12)owned_back=1;else owned_data=1;repaint();return 1;
 }
 u32 result=mo_previous_key(e);if(!mo_menu)preview=0;return result;
}
/* Le fond natif continue de se dessiner, y compris DrumSelect. Le menu est
 * dessine une seule fois apres la pile ; aucune fermeture/reouverture de vue. */
u32 mo_draw(u32 view,u32 canvas){if(mo_menu)return 0;return mo_previous_draw(view,canvas);}
u32 mo_stack(u32 view,u32 canvas){
 if(mo_menu&&!preview){
  /* Le fill natif arrondit les coins et laisse deux pixels du fond.
   * Bitmap128x64 du ViewManager :256mots, deux mots par colonne. */
  u32 *pixels=*(u32**)(canvas+16);for(u32 i=0;i<256;i++)pixels[i]=0;
  mo_previous_draw(view,canvas);
 }
 return mo_previous_stack(view,canvas);
}
void mo_frame(void){
 if(preview&&(!mo_menu||now()-stamp>=PREVIEW_TICKS)){preview=0;repaint();}
 mo_previous_frame();
}
