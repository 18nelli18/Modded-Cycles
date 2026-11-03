/* Banc prive : transport natif, vrais encodeurs filtre, snapshots/restauration.
 * Toutes les actions sont planifiees sur UI ; aucun setter depuis RPC/audio.
 * Les modificateurs virtuels ne sont visibles que pendant notre encodeur UI.
 */
typedef unsigned int u32;typedef int s32;typedef unsigned short u16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern void rp_old_request(const u8*),rp_old_send(u8*);
extern u32 rp_old_held(u32),rp_ui_encoder(u32,const volatile u32*),rp_queue_manager(u32*,const u32*,u32);
extern const u16*rp_params(u32);
extern void rp_deep_stop(u32);
extern void rp_clear_counters(void);
#ifdef RP_DEEP_WAKE
extern u32 rp_wake_status(void);
#endif
extern volatile u32 rp_menu;
static volatile u32 queued,status,serial,action,lane,sequence,reply,scope;
static volatile s32 delta;
static u8 restore[4],snap[6][6],volume[6];
u32 rp_held(u32 key){
 u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if(!(sr&0x700)&&((scope==1&&(key==2||key==5))||(scope==2&&key==1)))return 1;
 return rp_old_held(key);
}
static u32 pointer(u32 p){return p>=0x40400000u&&p<0x46a00000u&&!(p&3);}
static u32 safe(u32 app){
 if(!pointer(app))return 0;
 u32 sentinel=app+84,node=*(u32*)sentinel,n=0;
 while(node!=sentinel&&n++<16){
  if(!pointer(node))return 0;
  u32 view=*(u32*)(node+8);
  if(pointer(view)){
   u32 vt=*(u32*)view;
   if(vt==0x40111104||vt==0x40111544||vt==0x40111054)return 0;
  }
  node=*(u32*)node;
 }
 return node==sentinel;
}
static void refresh(void){
 for(u32 t=0;t<6;t++){
  const u16*p=rp_params(t);
  if(!p){for(u32 i=0;i<6;i++)snap[t][i]=255;volume[t]=255;continue;}
  snap[t][0]=p[24]>>8;snap[t][1]=p[25]>>8;snap[t][2]=p[20]>>8;snap[t][3]=p[21]>>8;snap[t][4]=p[9]>>8;snap[t][5]=1;
  volume[t]=p[26]>>8;
 }
}
static void tap_flags(u32 controller,u32 key,u32 flags){
 volatile u32 e[6];e[0]=0x400fc20c;e[1]=0;e[2]=*(volatile u32*)0xfc07000c;e[3]=key;e[4]=1|flags;e[5]=0;
 N(0x40077720)(controller,e);e[4]=16|flags;N(0x40077720)(controller,e);
}
static void tap(u32 controller,u32 key){tap_flags(controller,key,0);}
void rp_run(const void*unused){
 (void)unused;u32 app=N(0x400d0974)(),kind=action;status=3;
 if(!safe(app))goto done;
 if(kind==1||kind==10){if(kind==1)N(0x40059692)(0);tap(app+64,10);}
 else if(kind==2)tap(app+64,11);
 else if(kind==3||kind==9){tap(app+64,11);tap(app+64,11);if(kind==9)rp_deep_stop(1);else N(0x40058c04)(1);}
 else if(kind==11){tap(app+64,11);tap_flags(app+64,11,4);}
 else if(kind==12)rp_clear_counters();
 else if(kind==13){scope=2;tap_flags(app+64,5,2);scope=0;}
 else if(kind==14)tap(app+64,12);
 else if(kind==15){
  /* Vrai accord SETTINGS/PAGE, avec les deux releases; aucun latch virtuel. */
  volatile u32 e[6];e[0]=0x400fc20c;e[1]=0;e[2]=*(volatile u32*)0xfc07000c;e[3]=13;e[4]=1;e[5]=0;
  N(0x40077720)(app+64,e);tap(app+64,15);e[4]=16;N(0x40077720)(app+64,e);
 }
 else if(kind==4||kind==5){
  if(rp_menu)goto done;
  volatile u32 e[6];e[0]=0x400fbebc;e[1]=0;e[2]=*(volatile u32*)0xfc07000c;e[3]=kind==4?6:7;e[4]=(u32)delta;e[5]=0;
  scope=1;rp_ui_encoder(app+64,e);scope=0;
 }else if(kind==7){
  if(rp_menu||lane>=6)goto done;
  u32 root=N(0x400cf866)(),bank=root?N(0x4000eb9c)(root):0,obj=bank?N(0x40009c1a)(bank,lane):0;
  if(!obj)goto done;
  volatile u32 records[8];records[0]=24;records[1]=(u32)restore[0]<<24;records[2]=25;records[3]=(u32)restore[1]<<24;records[4]=20;records[5]=(u32)restore[2]<<24;records[6]=21;records[7]=(u32)restore[3]<<24;
  volatile u32 pair[2];pair[0]=(u32)records;pair[1]=(u32)(records+8);N(0x4001416c)(obj,pair);
 }
 refresh();status=2;
done:scope=0;serial++;queued=0;
}
static u32 equal(const u8*p,const char*s){for(u32 i=0;i<8;i++)if(p[i]!=(u8)s[i])return 0;return 1;}
void rp_request(const u8*msg){
 rp_old_request(msg);if(msg[8]!=2)return;
 const u8*p=*(const u8*const*)(msg+12),*end=*(const u8*const*)(msg+16);
 if(end<p||end-p<13)return;u32 len=end-p,kind=0;
 if(len==13&&equal(p+5,"SMQS318!")){reply=1;goto answer;}
 if(len==13&&equal(p+5,"SMVL318!")){reply=8;goto answer;}
#ifdef RP_DEEP_WAKE
 if(len==13&&equal(p+5,"SMWS318!")){reply=9;goto answer;}
#endif
 /* Les lectures par piste ont la meme longueur fixe que la version. */
 if(len==13&&p[5]=='S'&&p[6]=='M'&&p[7]=='R'&&p[8]>='0'&&p[8]<='5'&&p[9]=='3'&&p[10]=='1'&&p[11]=='8'&&p[12]=='!'){reply=2+p[8]-'0';goto answer;}
 if(len==13){
  if(equal(p+5,"SMPL318!"))kind=1;
  if(equal(p+5,"SMST318!"))kind=2;
  if(equal(p+5,"SMS2318!"))kind=3;
  if(equal(p+5,"SMRQ318!"))kind=6;
  if(equal(p+5,"SMDS318!"))kind=9;
  if(equal(p+5,"SMNP318!"))kind=10;
  if(equal(p+5,"SMN2318!"))kind=11;
  if(equal(p+5,"SMCP318!"))kind=12;
  if(equal(p+5,"SMPB318!"))kind=13;
  if(equal(p+5,"SMBK318!"))kind=14;
  if(equal(p+5,"SMGE348!"))kind=15;
 }
 if(len==14){if(equal(p+5,"SMFC318!"))kind=4;if(equal(p+5,"SMFR318!"))kind=5;}
 if(len==17&&p[5]=='S'&&p[6]=='M'&&p[7]=='W'&&p[8]>='0'&&p[8]<='5'&&p[9]=='3'&&p[10]=='1'&&p[11]=='8'&&p[12]=='!'){
  for(u32 i=0;i<4;i++)if(p[13+i]>127)return;
  kind=7;
 }
 if(!kind)return;
 reply=1;if(queued){status=4;goto answer;}
 action=kind;lane=p[8]-'0';delta=len==14?(s32)(signed char)p[13]:0;
 if(kind==7)for(u32 i=0;i<4;i++)restore[i]=p[13+i];
 queued=1;status=1;
 volatile u32 fn[4];fn[0]=fn[1]=0;fn[2]=(u32)rp_queue_manager;fn[3]=(u32)rp_run;N(0x400072c0)(N(0x400d0974)(),fn);
answer:sequence=((u32)p[0]<<8)|p[1];
}
void rp_send(u8*msg){
 rp_old_send(msg);if(!reply||msg[8]!=0x82)return;
 u8*p=*(u8**)(msg+12),*end=*(u8**)(msg+16);if(end<p||end-p!=15||(((u32)p[2]<<8)|p[3])!=sequence)return;
 u32 kind=reply;reply=0;u8*d=p+5;for(u32 i=0;i<10;i++)d[i]=0;d[0]='R';
#ifdef RP_DEEP_WAKE
 if(kind==9){u32 word=rp_wake_status();d[1]='W';d[2]=word;d[3]=word>>8;}
 else
#endif
 if(kind==8){d[1]='L';for(u32 i=0;i<6;i++)d[2+i]=volume[i];}
 else if(kind>=2){d[1]='V';for(u32 i=0;i<6;i++)d[2+i]=snap[kind-2][i];d[8]=kind-2;d[9]=status;}
 else{d[1]='S';d[2]=status;d[3]=queued;d[4]=serial>>24;d[5]=serial>>16;d[6]=serial>>8;d[7]=serial;d[8]=scope;d[9]=action;}
}
