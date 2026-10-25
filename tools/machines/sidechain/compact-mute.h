/* F2 preserve sans option active. F3 : delay dense3bits + six flags =392bits.
 * Memes49octets, CRC24 et reserves natives ; aucun champ natif ajoute. */
#define FXS_N 72
extern void fxp_capture(u8*),fxp_apply(const u8*);extern u32 fxp_crc(const u8*,u32),fxp_values_ok(const u8*);
extern volatile u8 sx_masks[6],du_config[6][5];extern void du_reset(void);
static u8 fxd_defaults[FXS_N];
static void fxd_init_defaults(void){for(u32 i=0;i<36;i++)fxd_defaults[i]=fxp_defaults[i];for(u32 i=0;i<6;i++){fxd_defaults[36+i]=60;u32 n=42+5*i;fxd_defaults[n]=0;fxd_defaults[n+1]=9;fxd_defaults[n+2]=0;fxd_defaults[n+3]=0;fxd_defaults[n+4]=6;}}
static void fxd_capture(u8*v){fxp_capture(v);for(u32 i=0;i<6;i++){v[36+i]=sx_masks[i];for(u32 k=0;k<5;k++)v[42+5*i+k]=du_config[i][k];}}
static void fxd_apply(const u8*v){fxp_apply(v);for(u32 i=0;i<6;i++){sx_masks[i]=v[36+i];for(u32 k=0;k<5;k++)du_config[i][k]=v[42+5*i+k];}du_reset();}
static u32 fxd_values_ok(const u8*v){if(!fxp_values_ok(v))return 0;for(u32 i=0;i<6;i++){u32 n=42+5*i;if(v[36+i]>63||v[n]>127||(v[n]&(1u<<i))||v[n+1]>15||v[n+2]>7||v[n+3]>3||v[n+4]>15)return 0;}return 1;}
static u32 fxd_width(u32 n){return n==0||n==18||n==20?4:7;}
static const u32 fxd_header[6]={29,30,31,36,37,39};
static void fxd_bits_put(u8*p,u32*bit,u32 value,u32 n){for(u32 i=0;i<n;i++,(*bit)++)if(value&(1u<<i))p[*bit>>3]|=1u<<(*bit&7);}
static u32 fxd_bits_get(const u8*p,u32*bit,u32 n){u32 v=0;for(u32 i=0;i<n;i++,(*bit)++)v|=((p[*bit>>3]>>(*bit&7))&1)<<i;return v;}
static u32 fxd_delay_rank(u32 id){u32 n=0;for(u32 i=0;i<id;i++)if(FXP_DEL_MASK&(1u<<i))n++;return n;}
static u32 fxd_delay_id(u32 rank){for(u32 i=0;i<32;i++)if(FXP_DEL_MASK&(1u<<i)){if(!rank)return i;rank--;}return 255;}
static void fxd_encode(u8*out,const u8*v,u32 valid){
 u8 payload[49]={0};u32 bit=0,extra=0;
 for(u32 i=0;i<48;i++)out[0x39d0+i]=0;
 for(u32 i=0;i<6;i++)out[0x3990+fxd_header[i]]=0;
 if(!valid)return;
 for(u32 i=0;i<6;i++)extra|=v[42+5*i]&64;
 for(u32 i=0;i<36;i++)fxd_bits_put(payload,&bit,i==20?v[i]-2u:extra&&i==18?fxd_delay_rank(v[i]):v[i],extra&&i==18?3:fxd_width(i));
 for(u32 i=0;i<6;i++)fxd_bits_put(payload,&bit,v[36+i],6);
 for(u32 i=0;i<6;i++){u32 n=42+5*i,mask=0,j=0;for(u32 t=0;t<6;t++)if(t!=i){if(v[n]&(1u<<t))mask|=1u<<j;j++;}fxd_bits_put(payload,&bit,mask,5);fxd_bits_put(payload,&bit,v[n+1],4);fxd_bits_put(payload,&bit,v[n+2],3);fxd_bits_put(payload,&bit,v[n+3],2);fxd_bits_put(payload,&bit,v[n+4],4);}
 if(extra)for(u32 i=0;i<6;i++)fxd_bits_put(payload,&bit,(v[42+5*i]>>6)&1,1);
 out[0x39d0]='F';out[0x39d1]=extra?'3':'2';u32 crc=fxp_crc(payload,49);out[0x39d2]=crc>>16;out[0x39d3]=crc>>8;out[0x39d4]=crc;
 for(u32 i=0;i<43;i++)out[0x39d5+i]=payload[i];for(u32 i=0;i<6;i++)out[0x3990+fxd_header[i]]=payload[43+i];
}
static u32 fxd_decode(const u8*in,u8*v){
 fxd_init_defaults();for(u32 i=0;i<FXS_N;i++)v[i]=fxd_defaults[i];const u8*p=in+0x39d0;
 if(p[0]=='F'&&p[1]=='X'&&p[2]=='S'&&p[3]=='1'){
  if(p[4]!=1||p[5]!=36||p[6]||p[7]||((u32)p[44]<<24|(u32)p[45]<<16|(u32)p[46]<<8|p[47])!=fxp_crc(p,44)||!fxp_values_ok(p+8))return 0;
  for(u32 i=0;i<36;i++)v[i]=p[8+i];return 1;
 }
 if(p[0]!='F'||(p[1]!='2'&&p[1]!='3'))return 0;
 u32 extra=p[1]=='3';u8 payload[49];for(u32 i=0;i<43;i++)payload[i]=p[5+i];for(u32 i=0;i<6;i++)payload[43+i]=in[0x3990+fxd_header[i]];
 if(((fxp_crc(payload,49)^((u32)p[2]<<16|(u32)p[3]<<8|p[4]))&0xffffff)||(!extra&&(payload[48]&0xf8)))return 0;
 u32 bit=0;for(u32 i=0;i<36;i++){v[i]=fxd_bits_get(payload,&bit,extra&&i==18?3:fxd_width(i));if(i==20)v[i]+=2;if(extra&&i==18)v[i]=fxd_delay_id(v[i]);}
 for(u32 i=0;i<6;i++)v[36+i]=fxd_bits_get(payload,&bit,6);
 for(u32 i=0;i<6;i++){u32 n=42+5*i,mask=fxd_bits_get(payload,&bit,5),j=0;v[n]=0;for(u32 t=0;t<6;t++)if(t!=i){if(mask&(1u<<j))v[n]|=1u<<t;j++;}v[n+1]=fxd_bits_get(payload,&bit,4);v[n+2]=fxd_bits_get(payload,&bit,3);v[n+3]=fxd_bits_get(payload,&bit,2);v[n+4]=fxd_bits_get(payload,&bit,4);}
 if(extra)for(u32 i=0;i<6;i++)v[42+5*i]|=fxd_bits_get(payload,&bit,1)<<6;
 return fxd_values_ok(v);
}
