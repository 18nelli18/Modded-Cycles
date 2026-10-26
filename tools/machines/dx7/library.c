/* Bibliotheque LEGACY : seize cartouches privees sur le disque interne.
 * SysEx non commercial7D/SML/1, checksum7bit ; aucune ecriture en IRQ.
 * Le navigateur est un overlay : aucune vue native n est remplacee. */
#include <stdint.h>
typedef uint32_t u32;typedef int32_t s32;typedef uint8_t u8;
#define N(a) ((u32(*)())(a))
extern void dx7_notice(const char*);
#ifdef DX7_BANK_GUARD
static const char *status_text;static u32 status_stamp;
void dx7_message(const char*text){status_text=text;status_stamp=*(volatile u32*)0xfc07000c;}
#define REPORT dx7_message
void dx7_status_draw(u32 canvas){
 if(!status_text)return;
 if(*(volatile u32*)0xfc07000c-status_stamp>
#ifdef DX7_BANK_CHUNKS
675840000u
#else
270336000u
#endif
){status_text=0;return;}
 N(0x40070efc)(canvas,8,4,119,20,0);N(0x40070c4e)(canvas,8,4,119,20,0xffffffffu);
 N(0x40071a04)(canvas,0x40ea14cc,13,8,0x10,"%s",status_text);
}
#else
#define REPORT dx7_notice
#endif
extern u32 dx7_valid(const u8*);extern void dx7_unpack(u8*,const u8*);
extern const u8 dx7_default_bank[32][156];
extern u32 dx7_library_load(u32),dx7_library_save(u32,const u8*);
static char names[16][17];static u32 scanned,available,browser,cursor,owned,back_owned;
#ifdef DX7_BANK_SAFE
#define BANK_MACHINES_KEY 5
#else
#define BANK_MACHINES_KEY 8
#endif
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
static void path(char*out,u32 slot,const char*ext){N(0x40000e6e)(out,"/Legacy%02u.%s",slot+1,ext);}
static u32 stopped(void){return *(volatile u32*)0x40a7883c!=1&&N(0x400d0a10)();}
static void scan(void){
 if(scanned||!stopped())return;scanned=1;
 for(u32 slot=0;slot<16;slot++){
  char p[24];u32 h[4]={0};path(p,slot,"nam");
  if(!N(0x4007bc5e)(p,"r",h)){
   u8 extra;u32 ok=N(0x4007baaa)(names[slot],16,h)==16&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);
   for(u32 j=0;j<16;j++)if((u8)names[slot][j]<32||(u8)names[slot][j]>126)ok=0;
   names[slot][16]=0;if(ok)available|=1u<<slot;
  }
 }
}
u32 dx7_library_packet(const u8*p,u32 length,u8*bank){
 /* F0 7D S M L 01 slot nom16 payload4096 checksum F7 =4121octets. */
 if(length!=4121||p[0]!=240||p[1]!=125||p[2]!=83||p[3]!=77||p[4]!=76||p[5]!=1||p[6]>=16||p[4120]!=247)return 0;
 u32 sum=0;for(u32 i=2;i<4120;i++){if(p[i]>127)return 0;sum+=p[i];}if(sum&127)return 0;
 for(u32 i=7;i<23;i++)if(p[i]<32||p[i]>126)return 0;
 for(u32 i=0;i<32;i++){dx7_unpack(bank+156*i,p+23+128*i);if(!dx7_valid(bank+156*i))return 0;}
 u32 slot=p[6];if(!dx7_library_save(slot,bank))return 0;
 char fn[24];path(fn,slot,"nam");u32 h[4]={0};if(N(0x4007bc5e)(fn,"w",h))return 0;
 u32 ok=!N(0x4007bb76)(h,0,16)&&N(0x4007bb0a)(p+7,16,h)==16;
 if(N(0x4007e2f6)(h))ok=0;if(N(0x4007bc1c)(h))ok=0;if(!ok)return 0;
 for(u32 i=0;i<16;i++)names[slot][i]=p[7+i];names[slot][16]=0;available|=1u<<slot;repaint();return 1;
}
u32 dx7_browser_key(const u32*e){
 if(!e)return 0;u32 code=e[3],down=e[4]&1,fresh=down&&!(e[4]&0x28);
 if(code==BANK_MACHINES_KEY&&owned){if(!down)owned=0;return 1;}
 if(code==12&&back_owned){if(!down)back_owned=0;return 1;}
 if(code==BANK_MACHINES_KEY&&fresh&&N(0x4007faf4)(1)){
  u32 kit=N(0x400cf866)(),lane=kit?N(0x40012412)(kit+48):0;
  if(((u8(*)(u32,u32))0x4001e318)(0,lane)==21){scan();browser=!browser;cursor=0;owned=1;repaint();return 1;}
 }
 if(!browser)return 0;
 if(code==12&&fresh){browser=0;back_owned=1;repaint();return 1;}
 if(code==32){if(!down){
   if(!stopped()){REPORT("STOP TO LOAD");return 1;}
   if(!cursor||(available&(1u<<(cursor-1)))){
    if(dx7_library_load(cursor)){browser=0;repaint();REPORT("LEGACY LOADED");}else REPORT("BANK READ ERROR");
   }
  }return 1;}
 return 0;
}
u32 dx7_browser_encoder(const u32*e){
 if(!browser||!e||e[0]!=0x400fbebc||e[3]!=1)return 0;
 s32 delta=(s32)N(0x4006f73a)(e,1,1);if(delta>0&&cursor<16)cursor++;if(delta<0&&cursor)cursor--;repaint();return 1;
}
u32 dx7_browser_draw(u32 view,u32 canvas){
 (void)view;if(!browser)return 0;
 N(0x40070efc)(canvas,5,3,122,60,0);N(0x40070c4e)(canvas,5,3,122,60,0xffffffffu);
 N(0x40071a04)(canvas,0x40ea14cc,12,49,0x10,"%s","LEGACY BANKS");
 u32 top=cursor?cursor-1:0;if(top>14)top=14;
 for(u32 i=top;i<top+3&&i<17;i++){
  const char*name=!i?"Factory":available&(1u<<(i-1))?names[i-1]:"Empty";char text[24];
  #ifdef DX7_BANK_SAFE
  char shortname[14];u32 j=0;for(;j<13&&name[j];j++)shortname[j]=name[j];shortname[j]=0;name=shortname;
#endif
  N(0x40000e6e)(text,"%02u %s",i,name);u32 y=35-12*(i-top);
  N(0x40071a04)(canvas,0x40ea14cc,11,y,0x10,"%s",text);
  if(i==cursor)N(0x40070f6e)(canvas,9,y-1,119,y+10,0xffffffffu);
 }
 return 1;
}
void *memset(void *p,int c,unsigned long n){volatile u8*d=(volatile u8*)p;while(n--)*d++=(u8)c;return p;}

#ifdef DX7_BANK_CHUNKS
#include "bank_chunks150.c"
#endif
