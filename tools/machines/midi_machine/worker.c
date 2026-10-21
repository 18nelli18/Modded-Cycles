/* CC coalesces par potard :72cases fixes, aucun malloc ni writer en IRQ.
 * Un seul token propre reveille la tache MIDI native. Elle traite au plus8CC
 * puis remet le token derriere les messages de notes deja en attente.
 */
typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;
#ifndef MM_MACHINE
#define MM_MACHINE 6
#endif
extern volatile u32 mm_assign_lane;
extern volatile u32 mm_page,mm_page_lane,mm_row,mm_edit;
extern u32 mm_cc_read(const u16 *,u32);
extern int mm_cc_number(u32);
extern u32 mm_cc_value(u32);
extern const u16 *mm_params(u32);
extern u32 mm_channel(const u16 *,u32);
extern u32 mm_port(const u16 *);
extern void mm_live_cleanup(void) __attribute__((weak));
extern void mm_live_cleanup_track(u32) __attribute__((weak));
static u8 mm_note_ports[16][128],mm_note_lanes[16][128];
static u32 mm_note_port,mm_note_owned,mm_note_lane,overridden;
/* Seule la tache native appelle ce routeur pour ses notes. Les autres appels
 * gardent AUTO=1 ; les fins de notes utilisent le port capture a l'attaque.
 */
void mm_note_route(u32 length,const u8 *bytes){
 u32 port=1,caller=(u32)__builtin_return_address(0);
 if(length==3&&bytes){
  u32 status=bytes[0]&0xf0,channel=bytes[0]&15,note=bytes[1];
  if(note<128&&(status==0x80||(status==0x90&&!bytes[2]))){
   u32 saved=mm_note_ports[channel][note];
   if(saved&0x80){port=saved&7;mm_note_ports[channel][note]=0;}
  }else if(note<128&&status==0x90&&mm_note_owned&&caller>=0x40089f00&&caller<0x4008a55a){
   port=mm_note_port;mm_note_ports[channel][note]=0x80|port;mm_note_lanes[channel][note]=mm_note_lane+1;
  }else if(status==0xb0&&(note==120||note==123)){
   for(u32 key=0;key<128;key++)if(mm_note_ports[channel][key]&0x80){
    u8 off[3]={0x80|channel,key,0};
    ((void (*)(u32,const u8 *,u32))0x400826b0)(3,off,mm_note_ports[channel][key]&7);
    mm_note_ports[channel][key]=0;
   }
  }
 }
 ((void (*)(u32,const u8 *,u32))0x400826b0)(length,bytes,port);
}
static volatile u32 pending[84],dirty[84],cursor,awake;
static const u32 mm_wakeup=0x7f4d4d00;
/* Parcourir Dest ne doit pas moduler tous les CC traverses. Lecture de quatre
 * mots UI seulement, sans getter ni allocation dans l'IRQ. Les CC manuels,
 * l'autre LFO et les autres pistes restent independants. */
static u32 destination_editing(u32 lane,u32 knob){
 return knob>=12&&knob<14&&mm_page==knob-11&&mm_page_lane==lane&&mm_row==2&&mm_edit;
}
static u16 lock(void){u16 old;__asm__ volatile("move.w %%sr,%0\nmove.w #0x2700,%%sr":"=d"(old)::"memory","cc");return old;}
static void unlock(u16 old){__asm__ volatile("move.w %0,%%sr"::"d"(old):"memory","cc");}
/* Sortie de machine : fermer seulement ses notes sur leurs anciens ports. */
void mm_leave(u32 lane){
 if(lane>=6)return;
 if(mm_live_cleanup_track)mm_live_cleanup_track(lane);
 for(u32 ch=0;ch<16;ch++)for(u32 note=0;note<128;note++){
  if(!(mm_note_ports[ch][note]&0x80)||mm_note_lanes[ch][note]!=lane+1)continue;
  u8 bytes[3]={0x80|ch,note,0};u32 port=mm_note_ports[ch][note]&7;
  mm_note_ports[ch][note]=0;mm_note_lanes[ch][note]=0;
  ((void (*)(u32,const u8 *,u32))0x400826b0)(3,bytes,port);
 }
 u16 sr=lock();for(u32 knob=0;knob<14;knob++)dirty[14*lane+knob]=0;unlock(sr);
}
static void wake(void){((void (*)(u32,const void *))0x40001fba)(0x40fcb2ec,&mm_wakeup);}
static void send(u32 value){
 u8 bytes[3]={value>>24,value>>16,value>>8};
 ((void (*)(u32,const u8 *,u32))0x400826b0)(3,bytes,value&255);
}
u32 mm_cc_put(u32 lane,u32 knob,u32 channel,u32 cc,u32 value,u32 port){
 if(lane==mm_assign_lane)return 0; /* Parcourir les numeros ne transmet rien. */
 if(destination_editing(lane,knob))return 0;
 if(lane>=6||knob>=14||channel>=16||cc>=128||value>=128||port<2||port>4)return 0;
 u32 slot=14*lane+knob,packet=((0xb0|channel)<<24)|(cc<<16)|(value<<8)|port;
 u16 old=lock();pending[slot]=packet;dirty[slot]=1;
 u32 notify=!awake;awake=1;unlock(old);
 if(notify)wake();
 return 1;
}
u32 mm_cc_worker(const void *packet){
 u16 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if(sr&0x700)return packet==&mm_wakeup;
 if(packet!=&mm_wakeup){
  const u8 *note=(const u8 *)packet;
  mm_note_owned=0;
  if(note&&(note[0]==5||note[0]==6)&&mm_live_cleanup)mm_live_cleanup();
  /* Le message de note natif peut preceder le token dans la mailbox. Publier
   * ses CC de piste avant l'attaque, au plus12, sans retarder les autres pistes.
   * Le worker conserve ensuite son traitement de notes/durees/STOP intact.
   */
  if(note&&note[0]==1&&note[8]<6){
   u32 lane=note[8];
   if(((u8 (*)(u32,u32))0x4001e318)(0,lane)==MM_MACHINE){
    const u16 *params=mm_params(lane);
    *(volatile u8 *)(0x40fdd580+lane)=mm_channel(params,lane);
    overridden|=1u<<lane;mm_note_lane=lane;mm_note_port=mm_port(params);mm_note_owned=1;
    for(u32 i=0;i<14;i++){
     u32 slot=14*lane+i;u16 old=lock();
     u32 value=dirty[slot]?pending[slot]:0;dirty[slot]=0;unlock(old);
     if(value&&lane!=mm_assign_lane&&!destination_editing(lane,i))send(value);
    }
   }else if(overridden&(1u<<lane)){
    *(volatile u8 *)(0x40fdd580+lane)=mm_channel((const u16 *)0,lane);
    overridden&=~(1u<<lane);
   }
  }
  return 0;
 }
 for(u32 count=0;count<8;count++){
  u32 value=0;u16 old=lock();
  for(u32 i=0;i<84;i++){
   u32 slot=cursor++;if(cursor==84)cursor=0;
   if(!dirty[slot])continue;
   value=pending[slot];dirty[slot]=0;
   if(slot/14==mm_assign_lane||destination_editing(slot/14,slot%14)){value=0;continue;}
   break;
  }
  if(!value){awake=0;unlock(old);return 1;}
  unlock(old);
  send(value);
 }
 /* awake reste1 : les producteurs peuvent remplacer pending sans multiplier
  * les tokens. Le prochain passage videra puis desarmera atomiquement. */
 wake();return 1;
}
/* Appel apres l'application native des locks, jamais dans le rendu DSP.
 * Les mots sont lus avant lissage audio : l'encodeur CC ne doit pas etre
 * interpole comme une valeur de synthese entre deux numeros de controleurs.
 */
extern volatile u32 mm_sequence_api[2];
u32 mm_sequence(u32 lane,const u32 *event,u32 time,u32 notes){
 if(lane>=6||!event)return 0;
 const u16 *params=(const u16 *)(0x800015aeu + 66*lane);
 if(params[9]!=(MM_MACHINE<<8))return 0;
 if(event[1]!=1)return 1;
 u32 channel=mm_channel(params,lane),port=mm_port(params);
 for(u32 knob=0;(params[32]==0x4d49||params[32]==0x4d4a||params[32]==0x4d4b)&&knob<12;knob++){
  u32 packed=mm_cc_read(params,knob);int cc=mm_cc_number(packed);
  if(cc>=0)mm_cc_put(lane,knob,channel,(u32)cc,mm_cc_value(packed),port);
 }
 /* La machine MIDI est toujours une sortie : le bit MOut audio du pattern
  * peut rester nul. Il ne doit pas supprimer les trigs de cette machine. */
 if(notes&&mm_sequence_api[1]){
  u8 *message=(u8 *)((u32 (*)(void))0x4008a5d0)();
  if(message){
   message[0]=1;*(u32 *)(message+4)=time;message[8]=lane;
   message[9]=event[7];message[10]=((const u8 *)event)[22];
   *(u32 *)(message+12)=event[13];
   ((void (*)(u32,void *))0x40001fba)(0x40fcb2ec,message);
  }
 }
 return 1;
}
