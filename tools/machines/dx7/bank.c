/* Cartouches DX7 : parser borne par port, validation hors interruption,
 * publication double banque ; aucune ROM Yamaha ou ressource tierce publique. */
#include <stdint.h>
typedef uint32_t u32;typedef uint8_t u8;
#define N(a) ((u32(*)())(a))
extern const u8 dx7_default_bank[32][156];
extern u32 dx7_din_original(u32);extern u32 dx7_usb_original(const u8*,u32);
extern void dx7_notice(const char*);
#ifdef DX7_BANK_GUARD
extern void dx7_message(const char*);
static u32 servicing;
#define REPORT dx7_message
#else
#define REPORT dx7_notice
#endif
static u8 banks[2][32][156];
static volatile u32 bank_ready,bank_active;
u32 dx7_imported,dx7_rejected;
#ifdef DX7_OPT
#define RX_BYTES 4121
extern u32 dx7_library_packet(const u8*,u32,u8*);
#ifdef DX7_BANK_CHUNKS
extern u32 dx7_chunk_packet(u32,const u8*,u32,u8*);
#endif
#else
#define RX_BYTES 4104
#endif
struct Rx{u8 data[RX_BYTES];u32 length,active;volatile u32 ready;};
static struct Rx rx[2];
#ifdef DX7_BANK_QUEUE
/* Producteur IRQ, consommateur UI : conserver une banque complete meme si
 * plusieurs messages USB arrivent avant le prochain rafraichissement. */
#define BANK_QUEUE_COUNT 40
struct BankFrame {u8 data[139];u32 length;};
struct BankQueue {struct BankFrame frames[BANK_QUEUE_COUNT];volatile u32 read,write,dropped;u32 handled;};
static struct BankQueue bank_queue[2] __attribute__((section(".bankchunks")));
extern void dx7_chunk_reset(u32);
static void queue_bank_frame(u32 port,const u8*p,u32 n){
 struct BankQueue*q=&bank_queue[port];u32 at=q->write,next=at+1;if(next==BANK_QUEUE_COUNT)next=0;
 if(n>139||next==q->read){q->dropped++;return;}
 for(u32 i=0;i<n;i++)q->frames[at].data[i]=p[i];q->frames[at].length=n;
 __asm__ volatile("":::"memory");q->write=next;
}
#endif
const u8 *dx7_patch(u32 index){return bank_ready?banks[bank_active][index&31]:dx7_default_bank[index&31];}
/* Limites exactes du format unpacked155 ; les noms sont ASCII7bits. */
u32 dx7_valid(const u8*p){
 static const u8 opmax[21]={99,99,99,99,99,99,99,99,99,99,99,3,3,7,3,7,99,1,31,99,14};
 static const u8 globmax[19]={99,99,99,99,99,99,99,99,31,7,1,99,99,99,99,1,5,7,48};
 for(u32 op=0;op<6;op++)for(u32 i=0;i<21;i++)if(p[op*21+i]>opmax[i])return 0;
 for(u32 i=0;i<19;i++)if(p[126+i]>globmax[i])return 0;
 for(u32 i=145;i<155;i++)if(p[i]>127)return 0;
 return p[155]<=63;
}
void dx7_unpack(u8*out,const u8*in){
 for(u32 k=0;k<6;k++){
  const u8*p=in+17*k;u8*q=out+21*k;
  for(u32 j=0;j<11;j++)q[j]=p[j];
  q[11]=p[11]&3;q[12]=(p[11]>>2)&3;q[13]=p[12]&7;q[20]=(p[12]>>3)&15;
  q[14]=p[13]&3;q[15]=(p[13]>>2)&7;q[16]=p[14];q[17]=p[15]&1;q[18]=(p[15]>>1)&31;q[19]=p[16];
 }
 for(u32 i=0;i<8;i++)out[126+i]=in[102+i];
 out[134]=in[110];out[135]=in[111]&7;out[136]=(in[111]>>3)&1;
 for(u32 i=0;i<4;i++)out[137+i]=in[112+i];
 out[141]=in[116]&1;out[142]=(in[116]>>1)&7;out[143]=(in[116]>>4)&7;out[144]=in[117];
 for(u32 i=0;i<10;i++)out[145+i]=in[118+i];out[155]=63;
}
void dx7_rx_byte(u32 port,u32 byte){
 if(port>=2||byte>255||byte>=248)return;struct Rx*r=&rx[port];
 if(r->ready)return;
 if(byte==240){r->length=0;r->active=1;}
 if(!r->active)return;
 if((byte&128)&&byte!=240&&byte!=247){r->active=r->length=0;return;}
 if(r->length>=RX_BYTES){r->active=r->length=0;return;}
 r->data[r->length++]=byte;
 if(r->length==2&&byte!=67
#ifdef DX7_OPT
 &&byte!=125
#endif
){r->active=r->length=0;return;}
 if(byte==247){
#ifdef DX7_BANK_QUEUE
  if(r->length>=6&&r->data[1]==125&&r->data[5]==2){
   queue_bank_frame(port,r->data,r->length);r->active=r->length=0;return;
  }
#endif
  r->active=0;__asm__ volatile("":::"memory");r->ready=1;}
}
#ifdef DX7_BANK_GUARD
/* Differer six octets au plus pour reconnaitre EXACTEMENT F0 7D S M L 01.
 * Les autres messages sont retransmis a l identique ; Clock/Start/Stop restent
 * immediats. Notre banque ne doit ni entrer dans le parseur OS ni etre recue
 * une seconde fois par son callback MIDI commun. Etat distinct USB/DIN. */
static u8 forward_head[2][6],usb_forward[4104];
static u32 forward_count[2];
static u32 forward_byte(u32 port,u8 b,u8*out){
 static const u8 header[6]={240,125,83,77,76,1};u32 n=forward_count[port];
 if(b>=248){out[0]=b;return 1;}
 if(n==7){
  if(b==247){forward_count[port]=0;return 0;}
  if(b==240){forward_head[port][0]=b;forward_count[port]=1;return 0;}
  if(b&128){forward_count[port]=0;out[0]=b;return 1;}return 0;
 }
 if(!n){if(b==240){forward_head[port][0]=b;forward_count[port]=1;return 0;}out[0]=b;return 1;}
 if(b==header[n]
#ifdef DX7_BANK_CHUNKS
 ||(n==5&&b==2)
#endif
 ){forward_head[port][n]=b;forward_count[port]=n==5?7:n+1;return 0;}
 for(u32 j=0;j<n;j++)out[j]=forward_head[port][j];forward_count[port]=0;
 if(b==240){forward_head[port][0]=b;forward_count[port]=1;return n;}
 out[n]=b;return n+1;
}
u32 dx7_din_rx(u32 byte){
 dx7_rx_byte(0,byte);u8 out[6];u32 n=forward_byte(0,(u8)byte,out),result=0;
 for(u32 i=0;i<n;i++)result=dx7_din_original(out[i]);return result;
}
u32 dx7_usb_rx(const u8*data,u32 length){
 if(length>65536)return dx7_usb_original(data,length);
 u32 result=0;
 for(u32 start=0;start<length;start+=4096){
  u32 end=start+4096;if(end>length)end=length;u32 n=0;
  for(u32 i=start;i<end;i++){dx7_rx_byte(1,data[i]);n+=forward_byte(1,data[i],usb_forward+n);}
  if(n)result=dx7_usb_original(usb_forward,n);
 }
 return result;
}
#else
u32 dx7_din_rx(u32 byte){dx7_rx_byte(0,byte);return dx7_din_original(byte);}
u32 dx7_usb_rx(const u8*data,u32 length){
 if(length<=4096)for(u32 i=0;i<length;i++)dx7_rx_byte(1,data[i]);
 return dx7_usb_original(data,length);
}
#endif
static u32 checksum(const u8*p,u32 n){u32 s=2166136261u;for(u32 i=0;i<n;i++)s=(s^p[i])*16777619u;return s;}
static u8 saved[5000];
static u32 bank_read(const char*path){
 u32 h[4]={0};u8 extra;if(N(0x4007bc5e)(path,"r",h))return 0;
 u32 ok=N(0x4007baaa)(saved,5000,h)==5000&&!N(0x4007baaa)(&extra,1,h);if(N(0x4007bc1c)(h))ok=0;
 if(!ok||saved[0]!=68||saved[1]!=88||saved[2]!=48||saved[3]!=49)return 0;
 u32 want=((u32)saved[4996]<<24)|((u32)saved[4997]<<16)|((u32)saved[4998]<<8)|saved[4999];
 if(checksum(saved+4,4992)!=want)return 0;
 for(u32 i=0;i<32;i++)if(!dx7_valid(saved+4+156*i))return 0;
 u32 next=bank_active^1;for(u32 i=0;i<4992;i++)((u8*)banks[next])[i]=saved[4+i];
 __asm__ volatile("":::"memory");bank_active=next;bank_ready=1;return 1;
}
static u32 bank_write(const char*path,const u8*data){
 saved[0]=68;saved[1]=88;saved[2]=48;saved[3]=49;
 for(u32 i=0;i<4992;i++)saved[4+i]=data[i];u32 s=checksum(saved+4,4992);
 for(u32 i=0;i<4;i++)saved[4996+i]=(u8)(s>>(24-i*8));u32 h[4]={0};
 if(N(0x4007bc5e)(path,"w",h))return 0;
 u32 ok=!N(0x4007bb76)(h,0,5000)&&N(0x4007bb0a)(saved,5000,h)==5000;
 if(N(0x4007e2f6)(h))ok=0;if(N(0x4007bc1c)(h))ok=0;return ok;
}
static void file_write(void){(void)bank_write("/Dx7Bank.cfg",(const u8*)banks[bank_active]);}
#ifdef DX7_OPT
u32 dx7_library_save(u32 slot,const u8*data){
 if(slot>=16)return 0;char path[24];N(0x40000e6e)(path,"/Legacy%02u.cfg",slot+1);return bank_write(path,data);
}
u32 dx7_library_load(u32 index){
 if(index>16)return 0;
 if(!index){u32 next=bank_active^1;for(u32 i=0;i<4992;i++)((u8*)banks[next])[i]=((const u8*)dx7_default_bank)[i];bank_active=next;bank_ready=1;}
 else{char path[24];N(0x40000e6e)(path,"/Legacy%02u.cfg",index);if(!bank_read(path))return 0;}
 file_write();return 1;
}
#endif
void dx7_service(void){
 if(*(volatile u32*)0x40a7883c==1||!N(0x400d0a10)())return;
 #ifdef DX7_BANK_GUARD
 if(servicing)return;servicing=1;
#endif
 static u32 loaded;if(!loaded){loaded=1;bank_read("/Dx7Bank.cfg");}
 for(u32 port=0;port<2;port++){
#ifdef DX7_BANK_QUEUE
  struct BankQueue*q=&bank_queue[port];
  if(q->handled!=q->dropped){
   q->handled=q->dropped;q->read=q->write;dx7_chunk_reset(port);dx7_rejected++;REPORT("BANK RX FULL");
  }else{
   /* Nombre borne ; une interruption peut ajouter des messages sans prolonger
    * indefiniment ce passage UI. Ne liberer le slot qu'apres sa lecture. */
   u32 end=q->write;
   while(q->read!=end){
    u32 at=q->read;struct BankFrame*f=&q->frames[at];
    if(q->handled!=q->dropped)break;
    u32 result=dx7_chunk_packet(port,f->data,f->length,(u8*)banks[bank_active^1]);
    if(result==2)dx7_imported++;else if(!result)dx7_rejected++;
    if(++at==BANK_QUEUE_COUNT)at=0;__asm__ volatile("":::"memory");q->read=at;
   }
  }
#endif
  struct Rx*r=&rx[port];if(!r->ready)continue;u32 n=r->length;const u8*p=r->data;
#ifdef DX7_OPT
#ifdef DX7_BANK_CHUNKS
  if(n>=6&&p[1]==125&&p[5]==2){
   u32 result=dx7_chunk_packet(port,p,n,(u8*)banks[bank_active^1]);if(result==2)dx7_imported++;else if(!result)dx7_rejected++;
   r->length=r->active=0;__asm__ volatile("":::"memory");r->ready=0;continue;
  }
#endif
  if(n>1&&p[1]==125){
   if(dx7_library_packet(p,n,(u8*)banks[bank_active^1])){dx7_imported++;REPORT("LEGACY BANK SAVED");}else dx7_rejected++;
   r->length=r->active=0;__asm__ volatile("":::"memory");r->ready=0;continue;
  }
#endif
  u32 bulk=n==4104&&p[3]==9&&p[4]==32&&p[5]==0;
  u32 single=n==163&&p[3]==0&&p[4]==1&&p[5]==27;
  u32 ok=(bulk||single)&&p[0]==240&&p[1]==67&&p[2]<16&&p[n-1]==247,sum=0;
  if(ok){for(u32 i=6;i<n-1;i++){sum+=p[i];if(p[i]>127)ok=0;}if(sum&127)ok=0;}
  u32 next=bank_active^1;
  if(ok){
   if(bulk){for(u32 i=0;i<32;i++){dx7_unpack(banks[next][i],p+6+i*128);if(!dx7_valid(banks[next][i]))ok=0;}}
   else{
    for(u32 i=0;i<32;i++)for(u32 j=0;j<156;j++)banks[next][i][j]=dx7_patch(i)[j];
    for(u32 i=0;i<155;i++)banks[next][0][i]=p[6+i];banks[next][0][155]=63;ok=dx7_valid(banks[next][0]);
   }
  }
  if(ok){__asm__ volatile("":::"memory");bank_active=next;bank_ready=1;dx7_imported++;file_write();REPORT(bulk?"DX BANK LOADED":"DX VOICE TO 0");}
  else dx7_rejected++;
  r->length=r->active=0;__asm__ volatile("":::"memory");r->ready=0;
 }
#ifdef DX7_BANK_GUARD
 servicing=0;
#endif
}
