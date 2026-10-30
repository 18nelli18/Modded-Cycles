/* Ecran128x64 : coordonnees explicites, police5x7 et quatre lignes fixes.
 * Le rendu ne depend pas des largeurs ni des marges du MenuView natif. */
#include "song.h"
typedef song_u32 u32;
#define N(a) ((u32(*)())(a))
extern song sg_song;extern volatile u32 sg_cursor,sg_active,gc_tree_cursor;
static const unsigned char glyphs[][5]={
{62,81,73,69,62},{0,66,127,64,0},{66,97,81,73,70},{33,65,69,75,49},{24,20,18,127,16},
{39,69,69,69,57},{60,74,73,73,48},{1,113,9,5,3},{54,73,73,73,54},{6,73,73,41,30},
{126,17,17,17,126},{127,73,73,73,54},{62,65,65,65,34},{127,65,65,34,28},{127,73,73,73,65},
{127,9,9,9,1},{62,65,73,73,122},{127,8,8,8,127},{0,65,127,65,0},{32,64,65,63,1},
{127,8,20,34,65},{127,64,64,64,64},{127,2,12,2,127},{127,4,8,16,127},{62,65,65,65,62},
{127,9,9,9,6},{62,65,81,33,94},{127,9,25,41,70},{70,73,73,73,49},{1,1,127,1,1},
{63,64,64,64,63},{31,32,64,32,31},{63,64,56,64,63},{99,20,8,20,99},{7,8,112,8,7},{97,81,73,69,67}};
static void fill(u32 c,int x,int y,int w,int h,u32 color){if(w>0&&h>0)N(0x40070dea)(c,x,64-y-h,x+w-1,63-y,color);}
static void box(u32 c,int x,int y,int w,int h){fill(c,x,y,w,1,~0u);fill(c,x,y+h-1,w,1,~0u);fill(c,x,y,1,h,~0u);fill(c,x+w-1,y,1,h,~0u);}
static void text(u32 c,int x,int y,const char*s,u32 color){for(;*s;s++,x+=6){unsigned char ch=*s;if(ch>='a'&&ch<='z')ch-=32;int index=ch>='0'&&ch<='9'?ch-'0':ch>='A'&&ch<='Z'?10+ch-'A':-1;if(index<0)continue;for(int col=0;col<5;col++)for(int bit=0;bit<7;bit++)if(glyphs[index][col]&(1u<<bit))fill(c,x+col,y+bit,1,1,color);}}
static void number(char*out,u32 n){out[0]='0'+n/10;out[1]='0'+n%10;out[2]=0;}
void sg_grid_draw(u32 view,u32 c){
 (void)view;fill(c,0,0,128,64,0);fill(c,0,0,128,11,~0u);text(c,2,2,"SONG",0);text(c,48,2,sg_song.loop?"LOOP":"STOP",0);
 u32 playing=*(volatile u32*)0x40a78874||*(volatile u32*)0x40a7883c;text(c,playing?102:102,2,playing?"PLAY":"STOP",0);
 u32 first=sg_cursor>=4?sg_cursor-3:0;
 for(u32 line=0;line<4;line++){
  u32 index=first+line;if(index>=sg_song.count)break;const song_row*r=&sg_song.rows[index];int y=13+12*line;char n[3],p[4],repeat[3];number(n,index+1);p[0]='A'+r->pattern/16;number(p+1,1+r->pattern%16);number(repeat,r->repeats);
  if(index==sg_cursor)fill(c,0,y-1,15,11,~0u);text(c,1,y+1,n,index==sg_cursor?0:~0u);
  box(c,17,y-1,23,11);text(c,20,y+1,p,~0u);
  text(c,43,y+1,"X",~0u);text(c,49,y+1,r->repeats<10?repeat+1:repeat,~0u);
  for(u32 t=0;t<6;t++){int x=66+10*t;box(c,x,y-1,8,10);if(!(r->mutes&(1u<<t)))fill(c,x+2,y+1,4,6,~0u);}
 }
 fill(c,0,62,128,2,~0u);if(sg_song.count)fill(c,0,62,128*(sg_cursor+1)/sg_song.count,2,0);
}

