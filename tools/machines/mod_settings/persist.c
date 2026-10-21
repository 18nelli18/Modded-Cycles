/* Preferences globales privees : E/S uniquement UI, transport arrete. */
typedef unsigned int u32;typedef unsigned char u8;
volatile u32 ms_api[9] __attribute__((section(".data")))={0};
static u32 loaded,dirty,last;
#define P(i) (*(volatile u32*)ms_api[i])
#define N(a) ((u32(*)())(a))
static u32 flags(void){return !!P(0)|(!!P(1)<<1)|((!*(volatile u8*)ms_api[2])<<2)|(!!P(3)<<3)|(!!P(4)<<4);}
static u32 file(u32 write,u8 *buf){
 u32 h[4]={0,0,0,0},ok=0;u8 extra;
 if(N(0x4007bc5e)("/ModSetup.cfg",write?"w":"r",h))return 0;
 if(write){if(!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(buf,8,h)==8&&!N(0x4007e2f6)(h))ok=1;}
 else if(N(0x4007baaa)(buf,8,h)==8&&!N(0x4007baaa)(&extra,1,h))ok=1;
 if(N(0x4007bc1c)(h))ok=0;return ok;
}
static void service(void){
 if(*(volatile u32*)0x40a7883c==1||!N(0x400d0a10)())return;
 u8 b[8]={77,83,48,49,0,0,165,90};
 if(!loaded){
  loaded=1;
  if(file(0,b)&&b[0]==77&&b[1]==83&&b[2]==48&&b[3]==49&&b[4]<32&&b[5]==(u8)~b[4]&&b[6]==165&&b[7]==90){
   u32 v=b[4];P(0)=v&1;*(volatile u8*)ms_api[2]=!(v&4);P(3)=!!(v&8);P(4)=!!(v&16);
   if(!((u32(*)(u32))ms_api[5])(!!(v&2)))loaded=0;
  }
  last=flags();
 }
 if(dirty){u32 v=flags();if(v==last){dirty=0;return;}b[4]=v;b[5]=~v;if(file(1,b)){last=v;dirty=0;}}
}
u32 ms_draw(u32 view,u32 canvas){service();return ((u32(*)(u32,u32))ms_api[7])(view,canvas);}
u32 ms_key(const u32 *event){u32 was=P(8);u32 result=((u32(*)(const u32*))ms_api[6])(event);if(was&&!P(8))dirty=1;return result;}
void *memset(void *p,int v,u32 n){u8 *d=p;while(n--)*d++=v;return p;}
