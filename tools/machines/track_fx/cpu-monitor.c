/* Moniteur DX UI : aucun nouveau hook ni formatage dans l IRQ audio.
 * Instantane court atomique, repaint4Hz, framebuffer128x64 mis en cache. */
typedef unsigned int u32;typedef int s32;
#define N(a) ((u32(*)())(a))
extern volatile u32 dx_enabled,gb_last_total,gb_peak,gb_over,gb_sum,gb_blocks;
extern volatile u32 dt_cuts[6],dt_t5_s,dt_t5_l,dt_t5_valid,dx_new;
extern volatile u32 gr_diag_sum,gr_diag_blocks,dx_peak,dx_over,gb_mask;
extern volatile u32 wf_api[];
extern volatile u32 cal_back_armed;
extern u32 cpu_old_key(u32,const u32*),cpu_old_encoder(u32,const u32*),cpu_old_stack(u32,u32);
extern void cpu_old_frame(void);
volatile u32 cpu_open,cpu_page;
static u32 back_owned,data_owned,page_owned,dirty,stamp;
static u32 bp,bc,ba,bs,bl;
#define BACK_WINDOW 47308800u
static u32 pixels[256],snap[15];
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
static u32 pct(u32 t){return t>900218?999:(t*100+45056)/90112;}
void cpu_snapshot(void){
 u32 sr;__asm__ volatile("move.w %%sr,%0\nmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");
 snap[0]=gb_last_total;snap[1]=gb_peak;snap[2]=gb_over;snap[3]=gb_sum;snap[4]=gb_blocks;snap[5]=dx_new;
 snap[6]=*(volatile u32*)0x46732f10>>3;u32 slow=*(volatile u32*)0x46732f14>>8;if(slow<snap[6])snap[6]=slow;
 snap[7]=dt_t5_s;snap[8]=dt_t5_l;for(u32 t=0;t<6;t++)snap[9+t]=dt_cuts[t];
 __asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");dirty=1;
}
void cpu_reset(void){
 u32 sr;__asm__ volatile("move.w %%sr,%0\nmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");
 gb_peak=gb_over=gb_sum=gb_blocks=gb_mask=dx_peak=dx_over=dx_new=gr_diag_sum=gr_diag_blocks=0;
 dt_t5_s=dt_t5_l=dt_t5_valid=0;for(u32 t=0;t<6;t++)dt_cuts[t]=0;
 __asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");cpu_snapshot();repaint();
}
static void close(void){cpu_open=ba=bc=bp=0;dirty=1;repaint();}
u32 cpu_key(u32 view,const u32*e){
 if(!e)return cpu_old_key(view,e);u32 code=e[3],down=e[4]&1,fresh=down&&!(e[4]&0x28);
 if(code==12&&back_owned){if(!down)back_owned=0;return 1;}
 if(code==32&&data_owned){if(!down)data_owned=0;return 1;}
 if(code==15&&page_owned){if(!down)page_owned=0;return 1;}
 if(!dx_enabled){if(cpu_open)close();return cpu_old_key(view,e);}
 if(code==12&&fresh&&N(0x4007faf4)(13)&&!N(0x4007faf4)(1)&&!N(0x4007faf4)(2)&&!N(0x4007faf4)(5)){
  back_owned=1;if(wf_api[5])*(volatile u32*)wf_api[5]=1;
  if(cpu_open)close();else{cpu_open=1;cpu_page=0;stamp=*(volatile u32*)0xfc07000c;cpu_snapshot();repaint();}return 1;
 }
 if(cpu_open){
  if(code==12){
   u32 now=*(volatile u32*)0xfc07000c;
   if(down&&(e[4]&0x28))bc=ba=0;
   if(fresh&&!bp){
    bp=1;bs=now;bc=!N(0x4007faf4)(1)&&!N(0x4007faf4)(2)&&!N(0x4007faf4)(5)&&!N(0x4007faf4)(13);
    if(bc&&ba&&now-bl<=BACK_WINDOW){back_owned=1;cal_back_armed=0;close();return 1;}ba=0;
   }
   if(!down&&bp){bp=0;ba=bc&&now-bs<=BACK_WINDOW;bl=now;bc=0;}
  }else if(fresh){ba=bc=0;}
  if(code==32){if(fresh){data_owned=1;cpu_reset();}return 1;}
  if(code==15){if(fresh){page_owned=1;cpu_page^=1;dirty=1;repaint();}return 1;}
 }
 return cpu_old_key(view,e);
}
u32 cpu_encoder(u32 view,const u32*e){if(cpu_open)ba=bc=0;return cpu_old_encoder(view,e);}
void cpu_frame(void){
 cpu_old_frame();if(cpu_open&&!dx_enabled){close();return;}
 if(cpu_open){u32 now=*(volatile u32*)0xfc07000c;if(now-stamp>=33792000u){stamp=now;cpu_snapshot();repaint();}}
}
void cpu_legacy_gesture(const u32*e){(void)e;}
static const unsigned char glyphs[][5]={
{62,81,73,69,62},{0,66,127,64,0},{66,97,81,73,70},{33,65,69,75,49},{24,20,18,127,16},
{39,69,69,69,57},{60,74,73,73,48},{1,113,9,5,3},{54,73,73,73,54},{6,73,73,41,30},
{126,17,17,17,126},{127,73,73,73,54},{62,65,65,65,34},{127,65,65,34,28},{127,73,73,73,65},
{127,9,9,9,1},{62,65,73,73,122},{127,8,8,8,127},{0,65,127,65,0},{32,64,65,63,1},
{127,8,20,34,65},{127,64,64,64,64},{127,2,12,2,127},{127,4,8,16,127},{62,65,65,65,62},
{127,9,9,9,6},{62,65,81,33,94},{127,9,25,41,70},{70,73,73,73,49},{1,1,127,1,1},
{63,64,64,64,63},{31,32,64,32,31},{63,64,56,64,63},{99,20,8,20,99},{7,8,112,8,7},{97,81,73,69,67}};

/* Bitmap natif : deux mots par colonne, moitie haute dans le second mot. */
static void dot(u32 x,u32 y,u32 color){u32*i=&pixels[x*2+(y<32?1:0)],bit=1u<<(y&31);if(color)*i|=bit;else *i&=~bit;}
static void text(u32 x,u32 y,const char*s,u32 color){
 for(;*s&&x+5<=128;s++,x+=6){unsigned char c=*s;u32 index=c>='0'&&c<='9'?c-'0':c>='A'&&c<='Z'?10+c-'A':36;
  if(index<36){for(u32 col=0;col<5;col++)for(u32 bit=0;bit<7;bit++)if(glyphs[index][col]&(1u<<bit))dot(x+col,y+bit,color);}
  else if(c==':'){dot(x+2,y+2,color);dot(x+2,y+5,color);}
  else if(c=='+'){for(u32 k=0;k<5;k++){dot(x+k,y+3,color);dot(x+2,y+1+k,color);}}
  else if(c=='>'){dot(x+1,y+1,color);dot(x+2,y+2,color);dot(x+3,y+3,color);dot(x+2,y+4,color);dot(x+1,y+5,color);}
 }
}
static u32 capped(u32 n){return n>99999?99999:n;}
static void draw(void){
 for(u32 i=0;i<256;i++)pixels[i]=0;
 for(u32 x=0;x<128;x++)for(u32 y=0;y<9;y++)dot(x,y,1);
 text(1,1,cpu_page?"VOICE CUTS    PAGE >":"CPU LOAD      PAGE >",0);
 char line[32];
 if(!cpu_page){
  N(0x40000e6e)(line,"NOW %3u  PEAK %3u",pct(snap[0]),pct(snap[1]));text(1,12,line,1);
  u32 avg=snap[4]?((snap[3]/snap[4])*100+128)/256:0;
  N(0x40000e6e)(line,"MEAN %3u SUST %3u",avg>999?999:avg,(snap[6]*100+128)/256);text(1,22,line,1);
  N(0x40000e6e)(line,"OVER %4u CUT %5u",snap[2]>9999?9999:snap[2],capped(snap[5]));text(1,32,line,1);
 }else for(u32 row=0;row<3;row++){
  u32 a=snap[9+row*2],b=snap[10+row*2];
  N(0x40000e6e)(line,"T%u %2u%s   T%u %2u%s",row*2+1,a,a>=99?"+":" ",row*2+2,b,b>=99?"+":" ");text(1,12+row*10,line,1);
 }
 if(snap[7]||snap[8]){N(0x40000e6e)(line,"LAST T5 S%u L%u",(snap[7]*100+128)/256,(snap[8]*100+128)/256);text(1,42,line,1);}
 else text(1,42,"NO T5 CUT RECORDED",1);
 text(1,56,"DATA CLR BACK X2 EXIT",1);dirty=0;
}
u32 cpu_stack(u32 view,u32 canvas){
 if(!cpu_open||!dx_enabled)return cpu_old_stack(view,canvas);
 if(dirty)draw();u32*p=*(u32**)(canvas+16);for(u32 i=0;i<256;i++)p[i]=pixels[i];return 1;
}
