/* Integration privee : commandes natives reservees, migration UI, arp externe.
 * Aucun getter UI depuis l'interruption audio ; setters depuis le thread UI.
 */
typedef unsigned int u32;typedef unsigned short u16;typedef unsigned char u8;
extern const u16 *mm_params(u32);
extern void mm_setup(u16 *);
extern u32 mx_encoder_original(const u32 *);
extern void mx_poll_original(void);
extern u32 mx_live_on_original(u32,u32,u32);
extern u32 mx_parameter_original(u32,u32,u32,u32,u32,u32);
extern volatile u32 mi_mm_page,mi_mm_lane,mi_mm_row;
extern volatile u32 lm_enabled;
extern volatile u8 mx_arp_config[6];
extern volatile u32 mx_arp_ring;
static volatile u32 arp_inject=6;
static u32 selected(void){u32 p=((u32(*)(void))0x400cf866)();return ((u32(*)(u32))0x40012412)(p+48);}
/* Le setter du son MIDI sait afficher/borner Swing, mais son mot6 ne
 * modifie pas le timing du pattern. Publier aussi le reglage par le setter
 * de piste natif : il respecte SWING ALL et notifie le lecteur audio.
 * Les pas maintenus gardent le chemin Nudge natif, distinct du Swing de base. */
u32 mx_parameter(u32 obj,u32 id,u32 value,u32 lane,u32 record,u32 notify){
 u32 result=mx_parameter_original(obj,id,value,lane,record,notify);
 /* La vue des parametres utilise le vrai TrackAccessor (400fd204) pour
  * Swing : son setter a deja modifie le pattern. Seul le SoundAccessor
  * (400fd134) a besoin du pont. Relire son mot6 depuis la vue de piste
  * annulait sinon immediatement le mouvement physique du potard. */
 if(id!=23||lane>=6||!obj||*(u32 *)obj!=0x400fd134)return result;
 u16 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if(sr&0x700)return result;
 if(((u8(*)(u32,u32))0x4001e318)(0,lane)!=17)return result;
 u32 state=((u32(*)(void))0x400cf9a8)();
 if(state&&*(u8*)(state+357)&&(*(u32*)(state+348)||*(u32*)(state+352)))return result;
 const u16 *params=mm_params(lane);if(!params||params[6]>(30u<<8))return result;
 u32 root=((u32(*)(void))0x400cf866)(),pat=((u32(*)(u32))0x4000f208)(root);
 u32 track=((u32(*)(u32,u32))0x4000cfcc)(pat,lane);
 if(track)((void(*)(u32,u32))0x40016378)(track,params[6]>>8);
 return result;
}
static void prepare(u32 t){
 const u16 *before=mm_params(t);if(!before||before[32]==0x4d4b)return;
 u16 after[33];for(u32 i=0;i<33;i++)after[i]=before[i];mm_setup(after);
 u32 records[64],n=0;
 for(u32 i=1;i<33;i++)if(i!=9&&i!=10&&before[i]!=after[i]){records[2*n]=i;records[2*n+1]=(u32)after[i]<<16;n++;}
 if(n){u32 p=((u32(*)(void))0x400cf866)(),bank=((u32(*)(u32))0x4000eb9c)(p),obj=((u32(*)(u32,u32))0x40009c1a)(bank,t);
  u32 pair[2]={(u32)records,(u32)(records+2*n)};((void(*)(u32,u32*))0x4001416c)(obj,pair);
 }
}
u32 mx_encoder(const u32 *event){
 u32 t=selected();if(t<6&&((u32(*)(u32,u32))0x4001e318)(0,t)==17){
  prepare(t);
  if(event&&event[0]==0x400fbebc&&(event[3]==12||event[3]==13)){
   mi_mm_page=0;return 0; /* Menu, valeurs, bornes et locks du vrai OS. */
  }
 }
 return mx_encoder_original(event);
}
void mx_poll(void){
 u32 changed=0;
 for(u32 t=0;t<6;t++){
  if(((u32(*)(u32,u32))0x4001e318)(0,t)==17){prepare(t);continue;}
  u16 *p=(u16*)mm_params(t);if(p&&p[32]==0x4d4b){p[32]=0x4d4a;changed|=1u<<t;}
 }
 mx_poll_original();
 for(u32 t=0;t<6;t++)if(changed&(1u<<t)){
  u16 *p=(u16*)mm_params(t);if(p&&p[32]==0x4d4a)p[32]=0x4d4b;
 }
}
void mx_latch_event(const u32 *event){
 if(!lm_enabled||!event||event[3]!=1||(event[4]&0x29)!=1)return;
 if(!((u32(*)(u32))0x4007faf4)(2))return;
 /* Armer a l'appui FUNC pendant TRACK, sans fenetre dependante de sa duree. */
 *(volatile u8*)0x401487ed=1;*(volatile u8*)0x401487ec=1;
}
u32 mx_arp_wants(u32 t){
 if(t>=6)return 0;
 u32 p=((u32(*)(void))0x400cf866)(),pat=((u32(*)(u32))0x4000f208)(p);
 /* Meme alternative que les touches natives : RETRIG maintenu ou A. On. */
 u32 cfg=((u32(*)(u32))0x4000d0dc)(pat);
 if(!((u32(*)(u32))0x4007faf4)(4)&&!((u8(*)(u32,u32))0x4000ccc0)(cfg,t))return 0;
 u32 obj=((u32(*)(u32,u32))0x4000cfcc)(pat,t);if(!obj)return 0;
 u32 vt=*(u32*)obj,raw=((u32(*)(u32))*(u32*)(vt+40))(obj);
 return raw&&(*(u8*)(raw+512)&7)!=5;
}
void mx_arp_on(u32 t,u32 n,u32 v){
 u32 p=((u32(*)(void))0x400cf866)(),pat=((u32(*)(u32))0x4000f208)(p);
 u32 obj=((u32(*)(u32,u32))0x4000cfcc)(pat,t),vt=*(u32*)obj;
 u32 raw=((u32(*)(u32))*(u32*)(vt+40))(obj);
 mx_arp_config[t]=*(u8*)(raw+512);
 if(!mx_arp_ring)mx_arp_ring=((u32(*)(u32))0x400802e0)(8*32);
 /* Le getter natif rend un octet : les 24 bits hauts de d0 sont libres. */
 u32 rate=((u32(*)(u32))0x40016086)(obj)&255u;
 ((void(*)(u32,u32,u32,u32,u32,u32,u32))0x4008171e)(t,n,v,0x40,0,0xffffffffu,rate);
}
u32 mx_live_on(u32 t,u32 n,u32 v){
 if(arp_inject==t&&((u32(*)(u32,u32))0x4001e318)(0,t)==17)return 1;
 return mx_live_on_original(t,n,v);
}
