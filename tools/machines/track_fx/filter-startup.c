/* Sons neufs avant publication des handles : reporter seulement le type LOW.
 * L'initialiseur generique invalide une attente avant tout reemploi du buffer
 * (chargement de son/projet inclus). Aucun reset global au demarrage. */
typedef unsigned int u32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern u32 mf_old_filter_init(u8*,u32),mf_old_filter_new(u8*,u32);
extern u32 mf_old_filter_get(u32);
extern void mf_old_filter_frame(void),mf_filter_set(u32,u32);
static u8 *pending[6];
static u32 next;
static void forget(u8 *raw){for(u32 i=0;i<6;i++)if(pending[i]==raw)pending[i]=0;}
static int track(u8 *raw){
 u32 root=*(volatile u32*)0x40fe4228;if(!root)return -1;
 for(u32 t=0;t<6;t++){
  u32 obj=N(0x40009c1a)(root+116,t);if(!obj)continue;
  u32 vt=*(const u32*)obj;if(vt&&N(*(const u32*)(vt+40))(obj)==(u32)raw)return (int)t;
 }
 return -1;
}
static void resolve(void){
 for(u32 i=0;i<6;i++)if(pending[i]){
  int t=track(pending[i]);if(t>=0){pending[i]=0;mf_filter_set((u32)t,0);}
 }
}
u32 mf_filter_init(u8 *raw,u32 machine){forget(raw);return mf_old_filter_init(raw,machine);}
u32 mf_filter_new(u8 *raw,u32 machine){
 u32 result=mf_old_filter_new(raw,machine);
 if(raw&&track(raw)<0){
  for(u32 i=0;i<6;i++)if(!pending[i]){pending[i]=raw;return result;}
  pending[next]=raw;next=(next+1)%6;
 }
 return result;
}
u32 mf_filter_get(u32 t){resolve();return mf_old_filter_get(t);}
void mf_filter_frame(void){resolve();mf_old_filter_frame();}
