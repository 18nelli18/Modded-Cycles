/* Deux lignes au-dessus du graphique natif, sans toucher la valeur ni les reperes. */
typedef unsigned int u32;typedef int s32;
extern volatile u32 ch_mode;
extern u32 ch_previous_popup(u32,u32,u32,s32,u32,u32);
u32 ch_popup(u32 view,u32 canvas,u32 descriptor,s32 value,u32 flags,u32 last){
 u32 result=ch_previous_popup(view,canvas,descriptor,value,flags,last);
 u32 mode=ch_mode;
 if((descriptor!=39&&descriptor!=40)||mode<1||mode>2)return result;
 /* Le sprite anime occupe y8..29 ; seule la zone titre y33..63 est remplacee. */
 ((void(*)(u32,s32,s32,s32,s32,u32))0x40070efc)(canvas,0,33,63,63,0);
 void (*text)(u32,u32,s32,s32,u32,const char*,const char*)=(void*)0x40071a04;
 text(canvas,0x40ea14cc,32,52,2,"%s",mode==1?"ChI":"ChII");
 text(canvas,0x40ea14cc,32,40,2,"%s",descriptor==39?"Speed":"Depth");
 return result;
}
