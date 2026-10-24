/* Verrou du mode uniquement : les seize divisions restent momentanees.
 * Wrapper UI br_key ; aucun appel ajoute a l IRQ. BACK quitte ; edition protegee, transport simple transmis.
 * Timer natif135168ticks/ms, fenetre350ms ; comparaison non signee avec wrap. */
typedef unsigned int u32;
extern volatile u32 br_keys,br_cancel;
extern u32 bl_previous_track(u32,u32*);
extern u32 bl_native(u32*);
extern void br_popup(const char*);
u32 bl_latched,bl_physical,bl_armed,bl_last,bl_back_owned,bl_command_owned,bl_function;
static u32 raw(u32 *event,u32 code,u32 flags){u32 copy[6];for(u32 i=0;i<6;i++)copy[i]=event[i];copy[3]=code;copy[4]=flags;return bl_native(copy);}
static void leave(u32 *event){bl_latched=0;bl_armed=0;raw(event,4,0);raw(event,2,0);}
u32 bl_key(u32 *event){
 u32 code=event[3],flags=event[4],down=flags&1,fresh=down&&!(flags&0x28);
 if(code==1)bl_function=down;
 u32 bit=code==2?1:code==4?2:0,prior=bl_physical;
 if(bit){if(down)bl_physical|=bit;else bl_physical&=~bit;fresh=fresh&&!(prior&bit);}
 if(code==12&&bl_back_owned){if(!down)bl_back_owned=0;return 1;}
 if(code>=9&&code<=11){u32 mask=1u<<(code-9);if(bl_command_owned&mask){if(!down)bl_command_owned&=~mask;return 1;}
  if(bl_latched&&down&&(bl_function||(bl_physical&1))){bl_command_owned|=mask;return 1;}
 }
 if(bl_latched){
#ifdef FX_TEMP_SHORTCUTS
  if((code==5||code==13)&&bl_function)return bl_native(event);
#endif
  if(code==12&&fresh){leave(event);bl_back_owned=1;br_popup("RETRIG OFF");event[3]=2;event[4]=16;return 0;}
  if((code==5||code==8||code==13)&&fresh){leave(event);return bl_native(event);}
  if(bit)return 1;
  /* Stop/projet annule le DSP natif ; le prochain press intentionnel rearme. */
  if(fresh&&code>=16&&code<=31&&br_cancel){raw(event,4,0);raw(event,4,1);}
  return bl_native(event);
 }
 if(code==2&&!down)bl_armed=0;
 if(code==4&&fresh&&(bl_physical&1)){
  u32 now=*(volatile u32*)0xfc07000c;
  if(bl_armed&&now-bl_last<=47308800u){u32 result=bl_native(event);if(br_keys==3&&!br_cancel){bl_latched=1;bl_armed=0;br_popup("RETRIG LATCH");}return result;}
  bl_last=now;bl_armed=1;
 }
 return bl_native(event);
}

/* La TrackSelectionView native interprete REC/PLAY/STOP comme copier/effacer/coller.
 * En verrou, les controles simples passent a la vue transport sous-jacente.
 * FUNC/physical TRACK+transport est deja consomme par bl_key. */
u32 bl_track_keys(u32 view,u32 *event){if(bl_latched&&event[3]>=9&&event[3]<=11)return 0;return bl_previous_track(view,event);}
