/* F4 :404bits utiles + tag4bits + CRC24 =54octets reserves existants.
 * F2/F3 restent byte-identiques sans cible FX. Aucun champ natif nouveau. */
#define FXS_N 78
extern void fxp_capture(u8*),fxp_apply(const u8*);
extern u32 fxp_crc(const u8*,u32),fxp_values_ok(const u8*);
extern volatile u8 sx_masks[6],du_config[6][5],du_fx[6];
extern void du_reset(void);
static u8 fxd_defaults[FXS_N];
static void fxd_init_defaults(void){
 for(u32 i=0;i<36;i++)fxd_defaults[i]=fxp_defaults[i];
 for(u32 i=0;i<6;i++){fxd_defaults[36+i]=60;u32 n=42+5*i;fxd_defaults[n]=0;fxd_defaults[n+1]=9;fxd_defaults[n+2]=0;fxd_defaults[n+3]=0;fxd_defaults[n+4]=6;fxd_defaults[72+i]=0;}
}
static void fxd_capture(u8*v){fxp_capture(v);for(u32 i=0;i<6;i++){v[36+i]=sx_masks[i];for(u32 k=0;k<5;k++)v[42+5*i+k]=du_config[i][k];v[72+i]=du_fx[i];}}
static void fxd_apply(const u8*v){fxp_apply(v);for(u32 i=0;i<6;i++){sx_masks[i]=v[36+i];for(u32 k=0;k<5;k++)du_config[i][k]=v[42+5*i+k];du_fx[i]=v[72+i];}du_reset();}
static u32 fxd_values_ok(const u8*v){
 if(!fxp_values_ok(v))return 0;
 for(u32 i=0;i<6;i++){u32 n=42+5*i;if(v[36+i]>63||v[n]>127||(v[n]&(1u<<i))||v[n+1]>15||v[n+2]>7||v[n+3]>3||v[n+4]>15||v[72+i]>3)return 0;}
 return 1;
}
static u32 fxd_width(u32 n){return n==0||n==18||n==20?4:7;}
static const u32 fxd_header[6]={29,30,31,36,37,39};
static void fxd_bits_put(u8*p,u32*bit,u32 value,u32 n){for(u32 i=0;i<n;i++,(*bit)++)if(value&(1u<<i))p[*bit>>3]|=1u<<(*bit&7);}
static u32 fxd_bits_get(const u8*p,u32*bit,u32 n){u32 v=0;for(u32 i=0;i<n;i++,(*bit)++)v|=((p[*bit>>3]>>(*bit&7))&1)<<i;return v;}
static u32 fxd_delay_rank(u32 id){u32 n=0;for(u32 i=0;i<id;i++)if(FXP_DEL_MASK&(1u<<i))n++;return n;}
static u32 fxd_delay_id(u32 rank){for(u32 i=0;i<32;i++)if(FXP_DEL_MASK&(1u<<i)){if(!rank)return i;rank--;}return 255;}
static u32 fxd_pack(u8*p,const u8*v,u32 dense,u32 returns){
 u32 bit=0;
 for(u32 i=0;i<36;i++)fxd_bits_put(p,&bit,i==20?v[i]-2u:dense&&i==18?fxd_delay_rank(v[i]):v[i],dense&&i==18?3:fxd_width(i));
 for(u32 i=0;i<6;i++)fxd_bits_put(p,&bit,v[36+i],6);
 for(u32 i=0;i<6;i++){u32 n=42+5*i,mask=0,j=0;for(u32 t=0;t<6;t++)if(t!=i){if(v[n]&(1u<<t))mask|=1u<<j;j++;}fxd_bits_put(p,&bit,mask,5);fxd_bits_put(p,&bit,v[n+1],4);fxd_bits_put(p,&bit,v[n+2],3);fxd_bits_put(p,&bit,v[n+3],2);fxd_bits_put(p,&bit,v[n+4],4);}
 if(dense)for(u32 i=0;i<6;i++)fxd_bits_put(p,&bit,(v[42+5*i]>>6)&1,1);
 if(returns)for(u32 i=0;i<6;i++)fxd_bits_put(p,&bit,v[72+i],2);
 return bit;
}
static u32 fxd_unpack(const u8*p,u8*v,u32 dense,u32 returns){
 u32 bit=0;
 for(u32 i=0;i<36;i++){v[i]=fxd_bits_get(p,&bit,dense&&i==18?3:fxd_width(i));if(i==20)v[i]+=2;if(dense&&i==18)v[i]=fxd_delay_id(v[i]);}
 for(u32 i=0;i<6;i++)v[36+i]=fxd_bits_get(p,&bit,6);
 for(u32 i=0;i<6;i++){u32 n=42+5*i,mask=fxd_bits_get(p,&bit,5),j=0;v[n]=0;for(u32 t=0;t<6;t++)if(t!=i){if(mask&(1u<<j))v[n]|=1u<<t;j++;}v[n+1]=fxd_bits_get(p,&bit,4);v[n+2]=fxd_bits_get(p,&bit,3);v[n+3]=fxd_bits_get(p,&bit,2);v[n+4]=fxd_bits_get(p,&bit,4);}
 if(dense)for(u32 i=0;i<6;i++)v[42+5*i]|=fxd_bits_get(p,&bit,1)<<6;
 if(returns)for(u32 i=0;i<6;i++)v[72+i]=fxd_bits_get(p,&bit,2);
 return fxd_values_ok(v);
}
static void fxd_encode(u8*out,const u8*v,u32 valid){
 u8 p[51]={0},record[54]={0};u32 mute=0,returns=0;
 for(u32 i=0;i<48;i++)out[0x39d0+i]=0;for(u32 i=0;i<6;i++)out[0x3990+fxd_header[i]]=0;
 if(!valid)return;
 for(u32 i=0;i<6;i++){mute|=v[42+5*i]&64;returns|=v[72+i];}
 fxd_pack(p,v,mute||returns,returns);
 if(returns){
  record[0]=0xa0|(p[0]&15);u32 crc=fxp_crc(p,51);record[1]=crc>>16;record[2]=crc>>8;record[3]=crc;
  for(u32 i=0;i<50;i++)record[4+i]=(p[i]>>4)|(p[i+1]<<4);
 }else{
  record[0]='F';record[1]=mute?'3':'2';u32 crc=fxp_crc(p,49);record[2]=crc>>16;record[3]=crc>>8;record[4]=crc;
  for(u32 i=0;i<49;i++)record[5+i]=p[i];
 }
 for(u32 i=0;i<48;i++)out[0x39d0+i]=record[i];for(u32 i=0;i<6;i++)out[0x3990+fxd_header[i]]=record[48+i];
}
static u32 fxd_decode(const u8*in,u8*v){
 fxd_init_defaults();for(u32 i=0;i<FXS_N;i++)v[i]=fxd_defaults[i];const u8*p=in+0x39d0;
 if(p[0]=='F'&&p[1]=='X'&&p[2]=='S'&&p[3]=='1'){
  if(p[4]!=1||p[5]!=36||p[6]||p[7]||((u32)p[44]<<24|(u32)p[45]<<16|(u32)p[46]<<8|p[47])!=fxp_crc(p,44)||!fxp_values_ok(p+8))return 0;
  for(u32 i=0;i<36;i++)v[i]=p[8+i];return 1;
 }
 u8 record[54],payload[51]={0};for(u32 i=0;i<48;i++)record[i]=p[i];for(u32 i=0;i<6;i++)record[48+i]=in[0x3990+fxd_header[i]];
 if((record[0]&0xf0)==0xa0){
  payload[0]=record[0]&15;
  for(u32 i=0;i<50;i++){payload[i]|=record[4+i]<<4;payload[i+1]=record[4+i]>>4;}
  if((fxp_crc(payload,51)^((u32)record[1]<<16|(u32)record[2]<<8|record[3]))&0xffffff)return 0;
  return fxd_unpack(payload,v,1,1);
 }
 if(record[0]!='F'||(record[1]!='2'&&record[1]!='3'))return 0;
 u32 dense=record[1]=='3';for(u32 i=0;i<49;i++)payload[i]=record[5+i];
 if(((fxp_crc(payload,49)^((u32)record[2]<<16|(u32)record[3]<<8|record[4]))&0xffffff)||(!dense&&(payload[48]&0xf8)))return 0;
 return fxd_unpack(payload,v,dense,0);
}
