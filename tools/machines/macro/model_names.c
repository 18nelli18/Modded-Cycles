/* Noms des 47 modeles MACRO dans le popup natif. UI uniquement.
 * Le delegate conserve les controles et l'etat de la page ; seule la zone
 * numerique droite est redessinee avec la police native et deux lignes au plus.
 * Ni setter, ni parametre audio, ni valeur sauvegardee ne change.
 */
typedef unsigned int u32;
typedef int s32;
extern u32 macro_names_original(u32,u32,u32,s32,u32,u32);
#include "macro_model_labels.inc"

u32 macro_names_popup(u32 view,u32 canvas,u32 descriptor,s32 value,u32 flags,u32 last){
 u32 result=macro_names_original(view,canvas,descriptor,value,flags,last);
 if(descriptor!=102)return result;
 s32 model=value>>8;
 if(model<0)model=0;
 if(model>46)model=46;
 const char *a=macro_model_lines[model][0],*b=macro_model_lines[model][1];
 /* Le bas de la zone contient les reperes natifs, conserves tels quels. */
 ((void(*)(u32,s32,s32,s32,s32,u32))0x40070efc)(canvas,64,32,127,63,0);
 void (*text)(u32,u32,s32,s32,u32,const char*,const char*)=(void*)0x40071a04;
 if(*b){
  text(canvas,0x40ea14cc,96,49,2,"%s",a);
  text(canvas,0x40ea14cc,96,37,2,"%s",b);
 }else text(canvas,0x40ea14cc,96,43,2,"%s",a);
 return result;
}
