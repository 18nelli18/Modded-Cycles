/* Ne pas confondre gain de send memorise et signal. IRQ audio uniquement.
 * Apres boot/panic, le premier passage precede le rendu : ignorer ses anciens
 * buffers. Le passage delay suivant observe les voix du bloc courant et le
 * reveil DMA natif reste responsable du premier bloc audible.
 * Une queue deja reveillee conserve exactement sa politique precedente. */
typedef unsigned int u32;typedef int s32;
extern volatile u32 ei_started,ei_woken,ei_rev,ei_del,ei_ractive,ei_dactive;
extern volatile u32 ei_side,ei_side_on;
static void wake(void){
 *(volatile u32*)0x401b72ec=0;*(volatile u32*)0x401b72f0=0;*(volatile u32*)0x401b72fc=0;
}
u32 ei_present(void){
#ifdef EI_PANIC_STOCK
 /* Sentinel2 : panic explicite, pas un STOP ordinaire. Le dernier bloc
  * de fondu natif ne doit pas relancer une reverbe infinie remise a zero. */
 if(ei_started==2){
  u32 note=!!*(volatile u32*)0x40a7883c;
  for(u32 t=0;t<6&&!note;t++)note=!!*(volatile u32*)(0x42308828+t*0x31c+0x38);
  if(!note){*(volatile u32*)0x401b72ec=1;*(volatile u32*)0x401b72f0=1;*(volatile u32*)0x401b72fc=16384;return 0;}
  ei_started=1;
 }
#endif
 /* Transport actif : politique precedente exacte, y compris prefetch avant
  * les voix et rampes de premier bloc. Le nouveau garde cible l arret. */
 if(*(volatile u32*)0x40a7883c){
  u32 sent=0,present=ei_woken&&(ei_rev||ei_del||ei_ractive||ei_dactive);
  static const u32 address[4]={0x40a78bd0,0x40a78bb8,0x40a78b9c,0x40a78b80};
  for(u32 k=0;k<4&&!sent&&!present;k++){
   const volatile u32*p=(const volatile u32*)address[k];sent=!!(p[0]|p[1]|p[2]|p[3]|p[4]|p[5]);
  }
  if(sent)ei_woken=1;
  present|=sent;
  if(!ei_started){ei_started=1;if(!present){
   *(volatile u32*)0x401b72ec=1;*(volatile u32*)0x401b72f0=1;*(volatile u32*)0x401b72fc=16384;
  }}
  if(present)wake();
  return present;
 }
 if(!ei_started){
  ei_started=1;ei_woken=0;
  *(volatile u32*)0x401b72ec=1;*(volatile u32*)0x401b72f0=1;*(volatile u32*)0x401b72fc=16384;
  return 0;
 }
 if(ei_woken&&(ei_rev||ei_del||ei_ractive||ei_dactive)){wake();return 1;}
 const volatile s32*mid=(const volatile s32*)0x80001858;
 const volatile s32*side=(const volatile s32*)ei_side;
 const volatile u32*on=(const volatile u32*)ei_side_on;
 static const u32 gain[4]={0x40a78bd0,0x40a78bb8,0x40a78b9c,0x40a78b80};
 for(u32 t=0;t<6;t++){
  u32 routed=0;for(u32 k=0;k<4;k++)routed|=((const volatile u32*)gain[k])[t];
  if(!routed)continue;
  u32 stereo=side&&on&&on[t];
#ifdef EI_SCAN_UNROLL
  const volatile u32*m=(const volatile u32*)(mid+32*t);u32 energy=0;
  if(stereo){const volatile u32*s=(const volatile u32*)(side+32*t);
   for(u32 i=0;i<32;i+=4)energy|=m[i]|m[i+1]|m[i+2]|m[i+3]|s[i]|s[i+1]|s[i+2]|s[i+3];
  }else for(u32 i=0;i<32;i+=8)energy|=m[i]|m[i+1]|m[i+2]|m[i+3]|m[i+4]|m[i+5]|m[i+6]|m[i+7];
  if(energy){ei_woken=1;wake();return 1;}
#else
  for(u32 i=0;i<32;i++)if(mid[32*t+i]||(stereo&&side[32*t+i])){ei_woken=1;wake();return 1;}
#endif
 }
 return 0;
}
