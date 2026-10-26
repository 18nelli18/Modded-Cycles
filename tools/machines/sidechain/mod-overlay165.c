/* Menu Mod au-dessus des vues natives ; edition des sons sans perdre la page.
 * Thread UI uniquement. Le timeout/repaint precede le mutex de dessin. */
typedef unsigned int u32;
extern volatile u32 mo_menu;
extern u32 mo_previous_encoder(u32,const u32*),mo_previous_key(const u32*);
extern u32 mo_previous_draw(u32,u32),mo_previous_stack(u32,u32),mo_menu_encoder(const u32*);
extern void mo_previous_frame(void);
#define N(a) ((u32(*)())(a))
#define PREVIEW_TICKS 270336000u
static u32 preview,stamp,owned_back,owned_data,parameter_edit;
static u32 pop_valid,pop_view,pop_desc,pop_value,pop_flags,pop_last,knob;
extern u32 mo_previous_popup(u32,u32,u32,u32,u32,u32);

/* 159 : le parent natif dessine les noms AVANT son popup. Le replay opaque
 * doit capturer puis restituer aussi ce nom, avec son contexte de piste. */
static char pop_label[48];
static void capture_label(u32 view,u32 desc){
 pop_label[0]=0;if(!view)return;u32 vt=*(u32*)view;if(!vt)return;
 u32 get=*(u32*)(vt+128);if(!get)return;u32 obj=N(get)(view,~0u,desc);if(!obj)return;
 u32 name=*(volatile unsigned short*)0x4001e4ca==0x4eb9?*(volatile u32*)0x4001e4cc:0x4000b22a;
 const char*text=(const char*)N(name)(obj,desc);if(!text)return;
 u32 i=0;for(;i<47&&text[i];i++)pop_label[i]=text[i];pop_label[i]=0;
}
static void draw_label(u32 canvas){
 if(!pop_label[0])return;
 char lines[3][11];u32 count=0,pos=0;
 while(count<3&&pop_label[pos]){
  while(pop_label[pos]==' ')pos++;if(!pop_label[pos])break;
  u32 n=0,last_space=0;while(n<10&&pop_label[pos+n]){if(pop_label[pos+n]==' ')last_space=n;n++;}
  if(n==10&&pop_label[pos+n]&&pop_label[pos+n]!=' '&&last_space)n=last_space;
  for(u32 i=0;i<n;i++)lines[count][i]=pop_label[pos+i];lines[count][n]=0;pos+=n;while(pop_label[pos]==' ')pos++;count++;
 }
 if(pop_label[pos]&&count)lines[count-1][9]='~';
 N(0x40070efc)(canvas,0,33,63,63,0);
 for(u32 i=0;i<count;i++)N(0x40071a04)(canvas,0x40ea14cc,32,(count==1?47:count==2?52:55)-10*i,2,"%s",lines[i]);
}

static void clear(u32 canvas){u32*p=*(u32**)(canvas+16);for(u32 i=0;i<256;i++)p[i]=0;}
u32 mo_popup(u32 view,u32 canvas,u32 desc,u32 value,u32 flags,u32 last){
 if(preview&&parameter_edit&&pop_valid!=2){pop_valid=1;pop_view=view;pop_desc=desc;pop_value=value;pop_flags=flags;pop_last=last;capture_label(view,desc);}
 return mo_previous_popup(view,canvas,desc,value,flags,last);
}
extern u32 mo_previous_parameter_encoder(u32,const u32*);
extern void mo_previous_fx_bind(u32,u32);
extern u32 mo_fx_render(u32,u32);
static u32 fx_shadow[40];
static u32 popup_pixels[256],pixels_valid;
static u32 stable_pixels[256],stable_valid;
extern volatile u32 mo_cr_mode,mo_ch_mode;
/* Capturer les valeurs APRES le vrai setter, sans attendre un draw de la
 * page cachee. Les memes getters virtuels sont utilises par le popup natif. */
u32 mo_parameter_encoder(u32 view,const u32*e){
 u32 result=mo_previous_parameter_encoder(view,e);
 if(parameter_edit&&preview&&pop_valid!=2&&view&&e&&e[0]==0x400fbebc){
  u32 vt=*(u32*)view;if(vt){
   u32 desc=*(u32*)(view+0x230),get=*(u32*)(vt+128);
   if(desc&&get&&*(u32*)(view+0x22c)==e[3]){
    u32 obj=N(get)(view,~0u,desc);if(desc&&obj){u32 ovt=*(u32*)obj;
     if(ovt&&*(u32*)(ovt+28)){pop_value=N(*(u32*)(ovt+28))(obj,desc);
      capture_label(view,desc);pop_view=view;pop_desc=desc;pop_flags=0;pop_last=1;pop_valid=1;pixels_valid=0;}
    }
   }
  }
 }
 return result;
}
void mo_fx_bind(u32 obj,u32 field){
 mo_previous_fx_bind(obj,field);
 if(preview&&(mo_menu||parameter_edit)){fx_shadow[39]=field;pop_valid=2;pixels_valid=0;}
}
static u32 now(void){return *(volatile u32*)0xfc07000c;}
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
u32 mo_encoder(u32 view,const u32*e){
 if(!mo_menu||!e||e[0]!=0x400fbebc)return mo_previous_encoder(view,e);
 if(!N(0x4006f73a)(e,1,1))return 1;
 if(e[3]==1){preview=0;return mo_menu_encoder(e);}
 /* Les autres encodeurs gardent le trajet FX/MIDI/parametres natif complet.
  * Masquer seulement l'intercepteur de menu pendant cette delegation ; ne
  * jamais passer par ses dessinateurs pendant menu=0 (ils effacent les pages). */
 if(e[3]<2||e[3]>15)return 1;
 pop_valid=0;pixels_valid=0;knob=e[3];u32 saved=mo_menu;mo_menu=0;preview=1;parameter_edit=1;stamp=now();
 mo_previous_encoder(view,e);mo_menu=saved;parameter_edit=0;stamp=now();repaint();
 return 1;
}
u32 mo_key(const u32*e){
 if(!e)return mo_previous_key(e);u32 code=e[3],f=e[4];
 if(code==12&&owned_back){if(!(f&1))owned_back=0;return 1;}
 if(code==32&&owned_data){if(!(f&1))owned_data=0;return 1;}
 if(mo_menu&&preview&&(code==12||code==32)&&(f&0x29)==1){
  preview=0;if(code==12)owned_back=1;else owned_data=1;repaint();return 1;
 }
 u32 was=mo_menu,result=mo_previous_key(e);
 /* La release BACK ne doit jamais atteindre DrumSelect apres fermeture du menu. */
 if(was&&!mo_menu&&code==12&&(f&0x29)==1&&result)owned_back=1;
 if(!mo_menu&&!parameter_edit){preview=pop_valid=0;}return result;
}
/* Le fond natif continue de se dessiner, y compris DrumSelect. Le menu est
 * dessine une seule fois apres la pile ; aucune fermeture/reouverture de vue. */
u32 mo_draw(u32 view,u32 canvas){if(mo_menu||parameter_edit)return 0;return mo_previous_draw(view,canvas);}
static u32 fx_owns_label(void){u32 c=mo_cr_mode,h=mo_ch_mode;
 u32 special=c==5||c==9||c==10||c==11;
 if(pop_desc==26&&(special||c==1||c==2))return 1;
 if((pop_desc==37||pop_desc==38)&&special)return 1;
 if(pop_desc==27&&(h==1||h==2||h==3||h>=7))return 1;
 if((pop_desc==39||pop_desc==40)&&(h==7||h==8||h==11))return 1;
 return pop_desc==40&&h==10;
}
u32 mo_stack(u32 view,u32 canvas){
 /* present() peut dessiner immediatement avec mo_menu temporairement nul.
  * Le transaction d'edition conserve le dernier frame termine, jamais un
  * parent natif transitoire, meme avant capture du nouveau popup. */
 if(parameter_edit){u32*p=*(u32**)(canvas+16);for(u32 i=0;i<256;i++)p[i]=stable_valid?stable_pixels[i]:0;return 1;}

 if(mo_menu&&!preview){
  /* Le fill natif arrondit les coins et laisse deux pixels du fond.
   * Bitmap128x64 du ViewManager :256mots, deux mots par colonne. */
  u32 *pixels=*(u32**)(canvas+16);for(u32 i=0;i<256;i++)pixels[i]=0;
  mo_previous_draw(view,canvas);
 }
 u32 result=mo_previous_stack(view,canvas);
 /* ParameterPageView se trouve sous DrumSelect. Rejouer son vrai popup apres
  * toutes les vues ; sinon DrumSelect le recouvre des le prochain repaint. */
 if(mo_menu&&preview&&pop_valid){
  u32 *pixels=*(u32**)(canvas+16);
  if(!pixels_valid){
  clear(canvas);
  if(pop_valid==2)mo_fx_render((u32)fx_shadow,canvas);
  else{mo_previous_popup(pop_view,canvas,pop_desc,pop_value,pop_flags,pop_last);if(!fx_owns_label())draw_label(canvas);
   N(0x40070f6e)(canvas,0,0,63,63,0xffffffffu);}
  for(u32 i=0;i<256;i++)popup_pixels[i]=pixels[i];pixels_valid=1;
  }else for(u32 i=0;i<256;i++)pixels[i]=popup_pixels[i];

 }
 if(mo_menu){u32*p=*(u32**)(canvas+16);for(u32 i=0;i<256;i++)stable_pixels[i]=p[i];stable_valid=1;}else stable_valid=0;
 return result;
}
void mo_frame(void){
 if(preview&&!parameter_edit&&(!mo_menu||now()-stamp>=PREVIEW_TICKS)){preview=0;repaint();}
 mo_previous_frame();
}
