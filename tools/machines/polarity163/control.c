/* Fichier global par piste ; acces uniquement dans la tache UI. */
typedef unsigned int u32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#ifdef UI_IDLE210
extern u32 lp_input_quiet(void);
#define UI_QUIET() lp_input_quiet()
#else
#define UI_QUIET() 1
#endif

extern volatile u32 lp_one[6],lp_two[6],lp_dirty;
static u32 loaded;
void lp_frame(void){
 u32 h[4]={0};u8 b[30],extra;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/LfoPol.cfg","r",h)){
  u32 ok=N(0x4007baaa)(b,30,h)==30&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);
  if(b[0]!='L'||b[1]!='P'||b[2]!=1||b[3]!=12||b[28]!=165||b[29]!=90)ok=0;
  for(u32 i=0;i<12;i++)if(b[4+i]>1||b[16+i]!=(u8)~b[4+i])ok=0;
  if(ok)for(u32 i=0;i<6;i++){lp_one[i]=b[4+i];lp_two[i]=b[10+i];}
 }}
 if(lp_dirty&&UI_QUIET()&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c){
  b[0]='L';b[1]='P';b[2]=1;b[3]=12;b[28]=165;b[29]=90;
  for(u32 i=0;i<12;i++){b[4+i]=i<6?lp_one[i]:lp_two[i-6];b[16+i]=~b[4+i];}
  if(!N(0x4007bc5e)("/LfoPol.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,30)&&N(0x4007bb0a)(b,30,h)==30&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)lp_dirty=0;}
 }
}
