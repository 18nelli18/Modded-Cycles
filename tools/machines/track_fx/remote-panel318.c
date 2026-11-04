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
#ifdef RP_PATTERN
extern void rp_pattern_snapshot(u8*);
#endif
#ifdef RP_MACHINE_TEST
extern void rp_fx_commit(void);
#endif
#ifdef RP_ECO
extern volatile u32 rp_eco_calls,rp_eco_shed,rp_eco_max,rp_eco_seen;
#endif
static volatile u32 queued,status,serial,action,lane,sequence,reply,scope;
static volatile s32 delta;
static u8 restore[4],snap[6][6],volume[6];
#ifdef RP_MACHINE_TEST
static u16 parameter_snapshot[6][33];
static u32 parameter_lane,parameter_slot;
static u32 ui_flags;
extern volatile u32 rp_sample_slot[6],rp_sample_count[64],rp_sample_mode[6];
static u32 test_machine(u32 id){return id<=8||id==10||id==12||id==14||id==24;}
#ifdef RP_GOV
extern volatile u32 rp_gov_mode;extern void rp_gov_set(u32);
#endif

#endif
u32 rp_held(u32 key){
 u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if(!(sr&0x700)&&((scope==1&&(key==2||key==5))||(scope==2&&key==1)||(scope==3&&key==2)||(scope>=256&&scope<288&&key==scope-256)))return 1;
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
#ifdef RP_MACHINE_TEST
 u32 ui=N(0x400cf9a8)();ui_flags=ui?(!!(N(0x4006b978)(ui)&255))|((!!(N(0x4006ba76)(ui)&255))<<1)|((!!(N(0x4006bdfe)(ui)&255))<<2):255;
#endif
 for(u32 t=0;t<6;t++){
  const u16*p=rp_params(t);
  if(!p){for(u32 i=0;i<6;i++)snap[t][i]=255;volume[t]=255;continue;}
  snap[t][0]=p[24]>>8;snap[t][1]=p[25]>>8;snap[t][2]=p[20]>>8;snap[t][3]=p[21]>>8;snap[t][4]=p[9]>>8;snap[t][5]=1;
#ifdef RP_MACHINE_TEST
  for(u32 i=0;i<33;i++)parameter_snapshot[t][i]=p[i];
  u32 root=N(0x400cf866)(),bank=root?N(0x4000eb9c)(root):0;
  volume[t]=bank?(N(0x40009c5a)(bank,t)&255):255;
#else
  volume[t]=p[26]>>8;
#endif
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
#ifdef RP_MACHINE_TEST
 else if(kind==16){
  /* Banc seul : six machines stock, setter natif, transport arrete. */
  if(rp_menu||lane>=6||delta<0||!test_machine((u32)delta)||*(volatile u32*)0x40a7883c||*(volatile u32*)0x40a78874)goto done;
  u32 root=N(0x400cf866)(),bank=root?N(0x4000eb9c)(root):0,obj=bank?N(0x40009c1a)(bank,lane):0;
  if(!obj)goto done;N(0x4001477e)(obj,(u32)delta,0,0);
 }
 else if(kind==17||kind==18){
  if(rp_menu||*(volatile u32*)0x40a7883c||*(volatile u32*)0x40a78874)goto done;
  if(kind==18)rp_fx_commit();
  else{
   volatile u32 e[6];e[0]=0x400fbebc;e[1]=0;e[2]=*(volatile u32*)0xfc07000c;e[3]=restore[0]?15:14;e[5]=0;
   s32 turns=(s32)(signed char)restore[1];u32 count=turns<0?(u32)-turns:(u32)turns;if(!count)count=1;
   scope=3;for(u32 i=0;i<count;i++){e[4]=turns<0?(u32)-1:turns>0?1:0;rp_ui_encoder(app+64,e);}scope=0;
  }
 }
 else if(kind==19){
  /* Audition native sans enregistrer/editer les trigs du pattern. */
  u32 ui=N(0x400cf9a8)();if(rp_menu||!ui||*(volatile u32*)0x40a78874||(N(0x4006ba76)(ui)&255)||(N(0x4006b978)(ui)&255))goto done;
  for(u32 t=0;t<6;t++)if(restore[0]==6||restore[0]==t){
   if(restore[1])N(0x40019e7a)(0,t,60,restore[1],0xffffffffu);
   else N(0x40019c84)(0,t,60);
  }
 }
#ifdef RP_GOV
 else if(kind==23){rp_gov_set((u32)delta);}
#endif
 else if(kind==20){
  if(rp_menu||lane>=6)goto done;
  u32 root=N(0x400cf866)(),bank=root?N(0x4000eb9c)(root):0,obj=bank?N(0x40009c1a)(bank,lane):0;
  if(!obj)goto done;u32 records[2]={(u32)delta,((u32)restore[0]<<24)|((u32)restore[1]<<16)},pair[2]={(u32)records,(u32)(records+2)};N(0x4001416c)(obj,pair);
 }
 else if(kind==21){tap(app+64,(u32)delta);}
 else if(kind==22){
  /* Accord natif borne TRACK/TRIG ou PATTERN/TRIG, aucune touche latchee. */
  volatile u32 e[6];e[0]=0x400fc20c;e[1]=0;e[2]=*(volatile u32*)0xfc07000c;e[3]=restore[0];e[4]=1;e[5]=0;
  scope=256+restore[0];N(0x40077720)(app+64,e);tap(app+64,restore[1]);scope=0;e[4]=16;N(0x40077720)(app+64,e);
 }
#endif
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
#ifdef RP_ECO
 if(len==13&&equal(p+5,"SMEC355!")){reply=10;goto answer;}
 if(len==13&&equal(p+5,"SMET355!")){reply=11;goto answer;}
#endif
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
#ifdef RP_MACHINE_TEST
 if(len==14&&p[5]=='S'&&p[6]=='M'&&p[7]=='M'&&p[8]>='0'&&p[8]<='5'&&p[9]=='3'&&p[10]=='7'&&p[11]=='0'&&p[12]=='!'&&test_machine(p[13]))kind=16;
 if(len==15&&equal(p+5,"SMFX370!")&&p[13]<2&&(s32)(signed char)p[14]>=-16&&(s32)(signed char)p[14]<=16)kind=17;
 if(len==13&&equal(p+5,"SMFK370!"))kind=18;
 if(len==15&&equal(p+5,"SMNT370!")&&p[13]<=6&&p[14]<=127)kind=19;
 if(len==15&&equal(p+5,"SMPR370!")&&p[13]<6&&p[14]<33){parameter_lane=p[13];parameter_slot=p[14];reply=12;goto answer;}
 if(len==17&&equal(p+5,"SMPW370!")&&p[13]<6&&(p[14]>=10&&p[14]<=25)&&(((u32)p[15]<<8)|p[16])<=32512)kind=20;
 if(len==14&&equal(p+5,"SMKY370!")&&p[13]>=1&&p[13]<=32)kind=21;
 if(len==13&&equal(p+5,"SMUI370!")){reply=13;goto answer;}
 if(len==13&&equal(p+5,"SMTS370!")){reply=14;goto answer;}
 if(len==13&&equal(p+5,"SMTC370!")){reply=15;goto answer;}
 if(len==13&&equal(p+5,"SMTT370!")){reply=16;goto answer;}
 if(len==13&&equal(p+5,"SMWA370!")){reply=17;goto answer;}
#ifdef RP_PATTERN
 if(len==13&&equal(p+5,"SMPL374!")){reply=19;goto answer;}
#endif
#ifdef RP_GOV
 if(len==13&&equal(p+5,"SMGG372!")){reply=18;goto answer;}
 if(len==14&&equal(p+5,"SMGV372!")&&p[13]<2)kind=23;
#endif

 if(len==15&&equal(p+5,"SMCK370!")&&(p[13]==2||p[13]==3)&&p[14]>=16&&p[14]<(p[13]==2?22:32))kind=22;
#endif
 if(len==17&&p[5]=='S'&&p[6]=='M'&&p[7]=='W'&&p[8]>='0'&&p[8]<='5'&&p[9]=='3'&&p[10]=='1'&&p[11]=='8'&&p[12]=='!'){
  for(u32 i=0;i<4;i++)if(p[13+i]>127)return;
  kind=7;
 }
 if(!kind)return;
 reply=1;if(queued){status=4;goto answer;}
 action=kind;lane=p[8]-'0';delta=len==14?(s32)(signed char)p[13]:0;
 if(kind==7)for(u32 i=0;i<4;i++)restore[i]=p[13+i];
#ifdef RP_MACHINE_TEST
 if(kind==17||kind==19||kind==22){restore[0]=p[13];restore[1]=p[14];}
 if(kind==20){lane=p[13];delta=p[14];restore[0]=p[15];restore[1]=p[16];}
#endif
 queued=1;status=1;
 volatile u32 fn[4];fn[0]=fn[1]=0;fn[2]=(u32)rp_queue_manager;fn[3]=(u32)rp_run;N(0x400072c0)(N(0x400d0974)(),fn);
answer:sequence=((u32)p[0]<<8)|p[1];
}
void rp_send(u8*msg){
 rp_old_send(msg);if(!reply||msg[8]!=0x82)return;
 u8*p=*(u8**)(msg+12),*end=*(u8**)(msg+16);if(end<p||end-p!=15||(((u32)p[2]<<8)|p[3])!=sequence)return;
 u32 kind=reply;reply=0;u8*d=p+5;for(u32 i=0;i<10;i++)d[i]=0;d[0]='R';
#ifdef RP_MACHINE_TEST
 if(kind==12){u32 value=parameter_snapshot[parameter_lane][parameter_slot];d[1]='P';d[2]=parameter_lane;d[3]=parameter_slot;d[4]=value>>8;d[5]=value;return;}
 if(kind==13){d[1]='U';d[2]=ui_flags;d[3]=3;return;}
 if(kind==14){
  d[0]='T';d[1]='S';u32 raw=*(volatile u32*)0x40a7887c;
  d[2]=255;d[9]=!!*(volatile u32*)0x40a7883c;
  if(raw>=0x40400000u&&raw<=0x42400000u-30710&&!(raw&1)){
   d[2]=*(const volatile u8*)(raw+30709);
   for(u32 t=0;t<6;t++){const volatile u16*f=(const volatile u16*)(raw+722*t);for(u32 i=0;i<64;i++)d[3+t]+=!!(f[i]&1);}
  }return;
 }
 if(kind==15){d[0]='T';d[1]='C';for(u32 t=0;t<6;t++)d[2+t]=*(volatile u8*)(0x40a7886c+t);d[8]=*(volatile u32*)0x40a7883c;d[9]=*(volatile u32*)0x40a78874;return;}
 if(kind==16){d[0]='T';d[1]='T';u32 now=*(volatile u32*)0x8000184c,tempo=*(volatile u32*)0x40149310;for(u32 i=0;i<4;i++)d[2+i]=now>>(24-8*i);d[6]=tempo>>8;d[7]=tempo;d[8]=*(volatile u32*)0x40a78e10;d[9]=*(volatile u32*)0x40a78e14;return;}
 if(kind==17){d[0]='W';d[1]='A';u32 slot=rp_sample_slot[5],n=slot<64?rp_sample_count[slot]:0;d[2]=slot<64?slot:255;for(u32 i=0;i<4;i++)d[3+i]=n>>(24-8*i);d[7]=rp_sample_mode[5];d[8]=parameter_snapshot[5][9]>>8;d[9]=!!n;return;}
#ifdef RP_PATTERN
 if(kind==19){rp_pattern_snapshot(d);return;}
#endif
#ifdef RP_GOV
 if(kind==18){d[0]='G';d[1]='G';d[2]=rp_gov_mode;return;}
#endif


#endif
#ifdef RP_ECO
 if(kind==10||kind==11){
  u32 a=kind==10?rp_eco_calls:rp_eco_max,b=kind==10?rp_eco_shed:rp_eco_seen;
  d[0]='E';d[1]=kind==10?'C':'T';
  d[2]=a>>24;d[3]=a>>16;d[4]=a>>8;d[5]=a;
  d[6]=b>>24;d[7]=b>>16;d[8]=b>>8;d[9]=b;return;
 }
#endif
#ifdef RP_DEEP_WAKE
 if(kind==9){u32 word=rp_wake_status();d[1]='W';d[2]=word;d[3]=word>>8;}
 else
#endif
 if(kind==8){d[1]='L';for(u32 i=0;i<6;i++)d[2+i]=volume[i];
#ifdef RP_MACHINE_TEST
 d[8]=*(volatile u32*)0x800017ac&63;d[9]=*(volatile u32*)0x800017b0&63;
#endif
 }
 else if(kind>=2){d[1]='V';for(u32 i=0;i<6;i++)d[2+i]=snap[kind-2][i];d[8]=kind-2;d[9]=status;}
 else{d[1]='S';d[2]=status;d[3]=queued;d[4]=serial>>24;d[5]=serial>>16;d[6]=serial>>8;d[7]=serial;d[8]=scope;d[9]=action;}
}
