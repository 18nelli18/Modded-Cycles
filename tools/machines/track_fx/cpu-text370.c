/* ABI du text.constprop.0 livre : x=1 implicite, arguments y/chaine/couleur.
 * Colonnes bitmap directes, meme police et memes pixels ; aucun nouvel etat. */
typedef unsigned int u32;
extern u32 cpu_pixels370[256];
extern const unsigned char cpu_glyphs370[36][5];
void cpu_text370(u32 y,const char*s,u32 color){
 for(u32 x=1;*s&&x+5<=128;s++,x+=6){
  unsigned char c=*s;u32 index=c>='0'&&c<='9'?c-'0':c>='A'&&c<='Z'?10+c-'A':36;
  for(u32 col=0;col<5;col++){
   u32 bits=index<36?cpu_glyphs370[index][col]:c==':'?(col==2?36:0):c=='+'?(col==2?62:8):c=='>'?(col==1?34:col==2?20:col==3?8:0):0;
   u32*p=cpu_pixels370+2*(x+col);
   if(y<32){u32 b=bits<<y;if(color)p[1]|=b;else p[1]&=~b;
    if(y>25){b=bits>>(32-y);if(color)p[0]|=b;else p[0]&=~b;}
   }else{u32 b=bits<<(y-32);if(color)p[0]|=b;else p[0]&=~b;}
  }
 }
}
