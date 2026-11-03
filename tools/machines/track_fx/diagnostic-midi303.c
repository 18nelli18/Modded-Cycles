/* Requete privee de lecture : conserver exactement les dix octets alloues
 * de la reponse version. Aucun hook audio, formatage, fichier ni setter. */
typedef unsigned int u32;typedef unsigned char u8;
extern void dx_old_request(const u8*),dx_old_send(u8*);
extern volatile u32 dx_now,dx_peak,dx_over,dx_cuts,dx_lfo[3],dx_punch,dx_light;
extern volatile u32 dx_woken,dx_started,dx_mode,dx_enabled;
extern volatile u32 dx_rev,dx_del,dx_active_rev,dx_active_del,dx_requested;
#ifdef DX_IDLE_AUDIT
extern volatile u8 dx_quiet[];
extern volatile u32 dx_engines[];
#endif
static u32 pending,sequence;
static u32 get16(const u8*p){return ((u32)p[0]<<8)|p[1];}
static void put32(u8*p,u32 v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static u8 pct(u32 t){u32 p=t>900218?999:(t*100+45056)/90112;return p>255?255:p;}
void dx_request(const u8*msg){
 if(msg[8]==2){
  const u8*p=*(const u8*const*)(msg+12),*end=*(const u8*const*)(msg+16);pending=0;
  if(end>=p&&end-p==13&&p[5]=='S'&&p[6]=='M'&&p[9]=='3'&&p[10]=='0'&&p[11]=='3'&&p[12]=='!'){
   if(p[7]=='D'&&p[8]=='X')pending=1;
   if(p[7]=='C'&&p[8]=='T')pending=2;
   if(p[7]=='F'&&p[8]=='X')pending=3;
#ifdef DX_IDLE_AUDIT
   if(p[7]=='V'&&p[8]=='I')pending=4;
   if(p[7]=='E'&&p[8]>='0'&&p[8]<='5')pending=5+p[8]-'0';
   if(p[7]=='A'&&p[8]>='0'&&p[8]<='5')pending=11+p[8]-'0';
#endif
   sequence=get16(p);
  }
 }
 dx_old_request(msg);
}
void dx_send(u8*msg){
 dx_old_send(msg);
 u8*p=*(u8**)(msg+12),*end=*(u8**)(msg+16);
 if(msg[8]!=0x82||!pending||end<p||end-p!=15||get16(p+2)!=sequence)return;
 u32 kind=pending;pending=0;u8*d=p+5;d[0]='D';
 if(kind==1){
  d[1]='X';d[2]=pct(dx_now);d[3]=pct(dx_peak);
  d[4]=(!!dx_woken)|((!!dx_started)<<1)|((!!*(volatile u32*)0x401b72ec)<<2)|((!!*(volatile u32*)0x401b72f0)<<3)|((!!dx_mode)<<4)|((!!dx_enabled)<<6);
  d[5]=dx_punch;d[6]=dx_light;for(u32 i=0;i<3;i++)d[7+i]=dx_lfo[i];
 }else if(kind==2){d[1]='C';put32(d+2,dx_over);put32(d+6,dx_cuts);}
#ifdef DX_IDLE_AUDIT
 else if(kind>=11){
  const volatile u32*v=(const volatile u32*)(0x42308828+(kind-11)*0x31c);
  d[1]='A';put32(d+2,v[0x230/4]);put32(d+6,v[0x234/4]);
 }
 else if(kind>=5){
  u32 t=kind-5;const volatile u32*v=(const volatile u32*)(0x42308828+t*0x31c);
  d[1]='E';d[2]=t;d[3]=dx_quiet[t];put32(d+4,dx_engines[t]);d[8]=v[0x23c/4];d[9]=(!!v[0x230/4])|((!!v[0x234/4])<<1);
 }
 else if(kind==4){
  d[1]='I';d[2]=!!*(volatile u32*)0x40a7883c;
  d[3]=(!!*(volatile u32*)0x40a78e14)|((!!*(volatile u32*)0x40a78e10)<<1)|((!!dx_woken)<<2);
  for(u32 t=0;t<6;t++){
   const volatile u32*v=(const volatile u32*)(0x42308828+t*0x31c);
   d[4+t]=(dx_quiet[t]>=64)|((!!v[0x230/4])<<1)|((!!v[0x234/4])<<2)|((v[0x23c/4]==1)<<3)|((dx_engines[t]>5)<<4)|((dx_quiet[t]==0)<<5);
  }
 }
#endif
 else{d[1]='F';d[2]=dx_rev;d[3]=dx_active_rev;d[4]=dx_del;d[5]=dx_active_del;d[6]=dx_requested>>8;d[7]=dx_requested;u32 on=0;
  static const u32*const gain[4]={(const u32*)0x40a78bd0,(const u32*)0x40a78bb8,(const u32*)0x40a78b9c,(const u32*)0x40a78b80};
  for(u32 g=0;g<4;g++)for(u32 t=0;t<6;t++)if(gain[g][t])on|=1u<<g;d[8]=on;d[9]=3;
 }
}
