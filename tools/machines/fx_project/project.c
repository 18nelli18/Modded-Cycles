/* FXP1 dans le padding du projet v6 : aucune E/S annexe, aucun pointeur sauve.
 * Seuls codec projet et service UI sont detournes ; DSP/IRQ inchanges. */
typedef unsigned int u32;typedef unsigned char u8;
#include "fields.h"
extern u32 fxp_native_encode(u8*,const u8*,u32,u32,u32);
extern u32 fxp_native_decode(u8*,const u8*,u32);
extern u32 fxp_native_new(u32);
extern void fxp_native_service(void);
extern u32 fxp_native_draw(u32,u32);
extern void fxp_native_frame(void);
static u32 owner,pending;
static u8 candidate[FXP_FIELDS];
static u32 active_raw(void);
void fxp_sync(void);
#ifdef FX_PATTERN
extern void fxs_project_decode_begin(void),fxs_project_decode_end(u32,const u8*,u32),fxs_project_new(u32),fxs_adopt(u32,const u8*),fxs_ui(void),fxs_project_encode_end(void),fxs_restore(u32,const u8*);
extern u32 fxs_project_encode_begin(u32),fxs_revision(void);
void fxp_capture(u8*out);void fxp_apply(const u8*in);
#endif
#define OFF 0x1c0
static u32 rd(const u8*p){return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void wr(u8*p,u32 n){p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
u32 fxp_crc(const u8*p,u32 n){u32 c=~0u;while(n--){c^=*p++;for(u32 k=0;k<8;k++)c=c>>1^((0u-(c&1))&0xedb88320u);}return ~c;}
static void snapshot(u8*out){for(u32 i=0;i<FXP_FIELDS;i++)out[i]=(u8)*(volatile u32*)fxp_fields[i];}
static void publish(const u8*in){for(u32 i=0;i<FXP_FIELDS;i++)*(volatile u32*)fxp_fields[i]=in[i];}
static void copy(u8*out,const u8*in){for(u32 i=0;i<FXP_FIELDS;i++)out[i]=in[i];}
u32 fxp_values_ok(const u8*p){
 for(u32 i=0;i<FXP_FIELDS;i++)if(p[i]>127)return 0;
 if(p[20]<2||p[20]>16||p[0]>=32||p[18]>=32)return 0;
 return ((FXP_REV_MASK>>p[0])&1)&&((FXP_DEL_MASK>>p[18])&1);
}
u32 fxp_record_valid(const u8*p){
 if(rd(p)!=0x46585031||p[5]!=FXP_FIELDS||p[6]||p[7]||rd(p+60)!=fxp_crc(p,60))return 0;
 u32 start=44;
#ifdef FX_PATTERN
 if(p[4]==2){if(rd(p+44)!=0x50415431)return 0;start=48;}
 else if(p[4]!=1)return 0;
#else
 if(p[4]!=1)return 0;
#endif
 for(u32 i=start;i<60;i++)if(p[i])return 0;
 return fxp_values_ok(p+8);
}
static void encode_record(u8*out,const u8*values){
 for(u32 i=0;i<64;i++)out[i]=0;wr(out,0x46585031);out[4]=1;out[5]=FXP_FIELDS;
#ifdef FX_PATTERN
 out[4]=2;wr(out+44,0x50415431);
#endif
 for(u32 i=0;i<FXP_FIELDS;i++)out[8+i]=values[i];wr(out+60,fxp_crc(out,60));
}
u32 fxp_encode(u8*out,const u8*raw,u32 limit,u32 flags,u32 callback){
#ifdef FX_PATTERN
 if(!fxs_project_encode_begin((u32)raw))return 0;
#endif
 u8 values[FXP_FIELDS];u32 have=0;
 if(raw&&(u32)raw==pending){copy(values,candidate);have=1;}
 else if(raw&&((u32)raw==owner||(u32)raw==active_raw())){snapshot(values);have=1;}
 u32 result=fxp_native_encode(out,raw,limit,flags,callback);
#ifdef FX_PATTERN
 fxs_project_encode_end();
#endif
 /* Bit4 : le codec produit l en-tete complet et ses bornes v6. */
 if((result&255)&&have&&(flags&16)&&out&&rd(out)==0xbeefbace&&rd(out+4)==6)encode_record(out+OFF,values);
 return result;
}
u32 fxp_decode(u8*raw,const u8*in,u32 callback){
#ifdef FX_PATTERN
 fxs_project_decode_begin();
#endif
 u32 result=fxp_native_decode(raw,in,callback);
#ifdef FX_PATTERN
 fxs_project_decode_end((u32)raw,in,result&255);
#endif
 if((result&255)&&raw&&in){
  copy(candidate,fxp_record_valid(in+OFF)?in+OFF+8:fxp_defaults);
  pending=(u32)raw;
  /* Le chargement actif doit etre termine avant tout retour au sequenceur,
   * sans attendre le dessin d une vue particuliere. */
  if((u32)raw==active_raw())fxp_sync();
 }
 return result;
}
u32 fxp_new(u32 raw){u32 result=fxp_native_new(raw);if(raw){copy(candidate,fxp_defaults);pending=raw;
#ifdef FX_PATTERN
 fxs_project_new(raw);
#endif
 if(raw==active_raw())fxp_sync();}return result;}
static u32 active_raw(void){
 /* Le getter400cf866 CONSTRUIT le singleton s il manque. Les codecs sont
  * aussi appeles pendant ce constructeur : ne jamais le rappeler ici. Le
  * slot natif n est publie qu apres la fin du constructeur4001134e. */
 u32 p=*(volatile u32*)0x40fe4228;if(!p)return 0;
 u32 *vt=*(u32**)p;return vt&&vt[10]?((u32(*)(u32))vt[10])(p):0;
}
void fxp_sync(void){
 u32 raw=active_raw();if(!raw)return;
 if(pending==raw){
#ifdef FX_PATTERN
 fxs_adopt(raw,candidate);
#endif
 publish(candidate);owner=raw;pending=0;*(volatile u32*)FXP_MENU_ADDRESS=0;}
 else if(owner!=raw){
#ifdef FX_PATTERN
 fxs_adopt(raw,fxp_defaults);
#endif
 publish(fxp_defaults);owner=raw;*(volatile u32*)FXP_MENU_ADDRESS=0;}
}
void fxp_service(void){
 fxp_sync();u8 values[FXP_FIELDS];
#ifdef FX_PATTERN
 u32 seen=fxs_revision();
#endif
 snapshot(values);
 /* Les lecteurs historiques peuvent initialiser leurs drapeaux mais leurs
  * fichiers globaux ne doivent plus remplacer le contenu du projet actif. */
 fxp_native_service();
#ifdef FX_PATTERN
 fxs_restore(seen,values);
#else
 publish(values);
#endif
}
/* L appel de fx_service est partiellement inline dans fx_draw. Synchroniser
 * a l entree du vrai dessin, meme lorsque le transport saute le service. */
u32 fxp_draw(u32 view,u32 canvas){
 fxp_sync();u8 values[FXP_FIELDS];
#ifdef FX_PATTERN
 u32 seen=fxs_revision();
#endif
 snapshot(values);
 u32 result=fxp_native_draw(view,canvas);
#ifdef FX_PATTERN
 fxs_restore(seen,values);
#else
 publish(values);
#endif
 return result;
}
/* Le service commun precede toutes les vues, hors verrou de dessin. */
void fxp_frame(void){fxp_sync();
#ifdef FX_PATTERN
 fxs_ui();
#endif
 fxp_native_frame();}
#ifdef FX_PATTERN
void fxp_capture(u8*out){snapshot(out);}void fxp_apply(const u8*in){publish(in);}
#endif
