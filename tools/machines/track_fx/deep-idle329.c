/* Veille profonde privee, seulement apres la commande de banc explicite.
 * Reveiller avant le traitement audio, jamais apres la copie du bloc DAC.
 * Une file de notes/transport non vide doit aussi reveiller les pads et MIDI.
 */
typedef unsigned int u32;
extern void rw_panic_transport(u32);
extern u32 rw_old_audio(const u32*);
extern u32 rw_old_note(u32,u32,u32,u32,u32,u32,u32);
#ifdef RW_DOUBLE_STOP
extern void rw_old_sound_off(u32);
#endif
volatile u32 rw_state,rw_reason;
u32 rw_status(void){return rw_state|(rw_reason<<8);}
static void wake(u32 reason){rw_state=0;rw_reason=reason;rw_panic_transport(0);}
void rw_arm(u32 value){
 rw_panic_transport(value);
 rw_reason=0;rw_state=value?1:0;
}
#ifdef RW_DOUBLE_STOP
void rw_stop(u32 value){
 rw_old_sound_off(value);
 if(value&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c)rw_arm(1);
}
#endif
void rw_check(void){
 if(!rw_state)return;
 if(rw_state==1){
  if(!*(volatile u32*)0x40a78e14)return;
  rw_state=2;
 }
 if(*(volatile u32*)0x40a78874||*(volatile u32*)0x40a7883c)wake(1);
}
u32 rw_audio(const u32*frame){
 /* Les messages de fond partagent la file native : ne pas les prendre pour
  * une note. Ces trois masques sont publies APRES le decodage des trigs. */
 if(rw_state&&((frame[1]|frame[2]|frame[4])&63))wake(2);
 return rw_old_audio(frame);
}
u32 rw_note(u32 track,u32 note,u32 velocity,u32 source,u32 extra,u32 a,u32 b){
 /* Le producteur natif refuse deja des notes avant le frame audio si le
  * transport DAC dort. Reveiller avant ce garde pour MIDI ET pads. */
 if(rw_state&&track<6&&note<128&&velocity&&velocity<128)wake(3);
 return rw_old_note(track,note,velocity,source,extra,a,b);
}
