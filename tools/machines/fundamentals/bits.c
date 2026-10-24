/* SY BITS : fraction8.8 native, editions en centiemes, sans nouveau format.
 * Le record51 est partage : deleguer toutes les autres machines. */
typedef unsigned int u32;typedef signed int s32;typedef unsigned char u8;
extern u32 bf_native_edit(u32,u32,s32,s32,u32);
extern void bf_native_frame(void),bf_draw(void);
extern u32 bf_native_popup(u32,u32,u32,s32,u32,u32);
static u32 saved[4];
u32 bf_active(void){
 u32 root=((u32(*)(void))0x400cf866)();if(!root)return 0;
 u32 lane=((u32(*)(u32))0x40012412)(root+48);
 return lane<6&&((u8(*)(u32,u32))0x4001e318)(0,lane)==10;
}
static s32 rounded(s32 n,s32 d){return n<0?-((-n+d/2)/d):(n+d/2)/d;}
static s32 change(s32 value,s32 delta,u32 fine){
 s32 turns=delta<0?-((-delta+255)>>8):(delta+255)>>8;
 s32 result=fine?16384+rounded((rounded((value-16384)*100,256)+turns)*256,100):value+turns*256;
 return result<10240?10240:result>22528?22528:result;
}
u32 bf_step(u32 c,s32 v,s32 d,s32 lo,s32 hi){
 if(!bf_active())return ((u32(*)(u32,s32,s32,s32,s32))saved[0])(c,v,d,lo,hi);
 return change(v,d,0);
}
u32 bf_fine(u32 c,s32 v,s32 d,s32 lo,s32 hi){
 if(!bf_active())return ((u32(*)(u32,s32,s32,s32,s32))saved[1])(c,v,d,lo,hi);
 return change(v,d,1);
}
u32 bf_edit(u32 o,u32 desc,s32 v,s32 d,u32 original){
 if(desc==91&&bf_active())return change(v,d,0);
 return bf_native_edit(o,desc,v,d,original);
}
u32 bf_fmt(u32 c,u32 v,char*out){
 if(!bf_active())return ((u32(*)(u32,u32,char*))saved[2])(c,v,out);
 s32 cents=rounded(((s32)v-16384)*100,256);u32 mag=cents<0?-cents:cents;
 return ((u32(*)(char*,const char*,...))0x40000e6e)(out,"%s%d.%02d",cents<0?"-":"+",mag/100,mag%100);
}
u32 bf_original_draw(void){return saved[3];}
/* Meme ABI que le dessin natif (contexte,valeur,bitmap,x,y). Police5x7 :
 * six caracteres signes tiennent dans la demi-fenetre sans rogner le +. */
void bf_draw_text(u32 context,u32 value,u32 canvas,s32 x,s32 y){
 (void)context;char text[20];bf_fmt(0,value,text);
 ((void(*)(u32,u32,s32,s32,u32,const char*,...))0x40071a04)(canvas,0x40ea14cc,x,y,2,"%s",text);
}
/* Couche finale : le grand affichage SY utilise un autre dessinateur que
 * le callback du record partage. Effacer aussi sa legende mise en cache. */
u32 bf_popup(u32 view,u32 canvas,u32 desc,s32 value,u32 flags,u32 last){
 u32 result=bf_native_popup(view,canvas,desc,value,flags,last);
 if(desc!=91||!bf_active())return result;
 char text[20];bf_fmt(0,(u32)value,text);
 ((void(*)(u32,s32,s32,s32,s32,u32))0x40070efc)(canvas,64,0,127,63,0);
 ((void(*)(u32,u32,s32,s32,u32,const char*,...))0x40071a04)(canvas,0x40ea14cc,96,34,2,"%s",text);
 return result;
}
void bf_prepare(void){
 bf_native_frame();
 volatile u32 *rec=(volatile u32*)((u32(*)(u32))0x4004df40)(91);
 if(!rec||!rec[19]||!rec[20]||!rec[8])return;
 if(!saved[0]){saved[0]=rec[19];saved[1]=rec[20];saved[2]=rec[8];saved[3]=rec[12];}
 rec[19]=(u32)bf_step;rec[20]=(u32)bf_fine;rec[8]=(u32)bf_fmt;
 rec[12]=saved[3];
}
