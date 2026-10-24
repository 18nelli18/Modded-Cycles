/* Audit prive : trajectoire fade partagee entre voies identiques, note135.
 * Derive du repeat propre notes99/111, TinyGregAudio MIT (licence beat_repeat).
 * Aucun etat global ajoute ; cache sur pile, valide pour cet appel seulement.
 * Helpers DSP, quantification/historique/masques, restent ceux du firmware.
 */
typedef unsigned int u32;typedef signed int i32;typedef signed short i16;
#define N 131072u
#define MASK (N-1)
struct br_frame {u32 phase,envelope,wet,record;};
extern u32 br_valid,br_start,br_length,br_excluded,br_lane_wet[6],br_side,br_side_on,br_wet;
extern i32 br_active;
#ifdef RR_FAST_RECORD
extern volatile u32 br_keys;
#endif
extern i16 *volatile br_history;
#ifdef RR_LOCAL_PLAIN
/* Chemin plateau du profil no-filter, porte dans le profil filtre : memes bits. */
static __attribute__((noinline)) void rr_native_plain(i32 *channel,i16 *write,i16 *read,u32 record){
 if(record)for(u32 i=0;i<32;i++){
  i32 live=channel[i],q=live>>15;
  if(q>32767)q=32767;
  if(q< -32767)q=-32767;
  write[i]=(i16)q;
  i32 residual=(i32)(((u32)live&511u)^256u)-256;
  channel[i]=(i32)read[i]*32768+residual;
 }
 else for(u32 i=0;i<32;i++){
  i32 live=channel[i],residual=(i32)(((u32)live&511u)^256u)-256;
  channel[i]=(i32)read[i]*32768+residual;
 }
}
#else
extern void rr_native_plain(i32*,i16*,i16*,u32);
#endif
extern void rr_native_mode(i32*,i16*,u32,const struct br_frame*,const u32*,u32);
void rr_tracks(u32 now,const struct br_frame *frames){
 u32 mix[32],cached=0,cached_local=0,cached_excluded=0,cached_end=0;
 u32 write=now&MASK,read=(br_start+frames[0].phase)&MASK;
 u32 plain=br_length>=32&&frames[0].envelope==65536&&frames[31].envelope==65536
  &&frames[31].phase==frames[0].phase+31&&frames[0].record==frames[31].record
  &&write<=N-32&&read<=N-32;
 for(u32 lane=0;lane<6;lane++){
  u32 local=br_lane_wet[lane],excluded=!!(br_excluded&(1u<<lane));
  u32 mode=local==0&&(excluded||(frames[0].wet==0&&frames[31].wet==0))?2:
   (local==65536&&!excluded&&frames[0].wet==65536&&br_valid?1:0);
  if(!mode){
   if(cached&&local==cached_local&&excluded==cached_excluded)local=cached_end;
   else{
    cached=1;cached_local=local;cached_excluded=excluded;
    for(u32 i=0;i<32;i++){
     u32 goal=excluded?0:frames[i].wet;
     if(local<goal){local+=1024;if(local>goal)local=goal;}
     else if(local>goal)local=local-goal>1024?local-1024:goal;
     mix[i]=local;
    }
    cached_end=local;
   }
  }
  br_lane_wet[lane]=local;
  i32 *channel=(i32 *)(0x80001858+128*lane);i16 *history=br_history+N*lane;
  if(mode==1&&plain)rr_native_plain(channel,history+write,history+read,frames[0].record);
  else if(!(mode==2&&plain&&!frames[0].record))rr_native_mode(channel,history,now,frames,mix,mode);
  if(br_side&&((u32 *)br_side_on)[lane]){
   channel=(i32 *)(br_side+128*lane);history=br_history+N*(lane+6);
   if(mode==1&&plain)rr_native_plain(channel,history+write,history+read,frames[0].record);
   else if(!(mode==2&&plain&&!frames[0].record))rr_native_mode(channel,history,now,frames,mix,mode);
  }
 }
}

#if defined(RR_LOCAL_PLAIN) || defined(RR_FAST_RECORD)
static u32 render_plain_block(u32 now,i32 target){
 if(!br_valid||target<0||target!=br_active||br_wet!=65536)return 0;
 u32 length=br_length,elapsed=now-br_start,phase=elapsed%length;
 u32 ramp=length/4;if(ramp>32)ramp=32;if(!ramp)ramp=1;
 u32 scale=65536/ramp,edge=(65536+scale-1)/scale;
 if(phase<edge||length-phase<31+edge)return 0;
 u32 record=elapsed<length||((elapsed&MASK)>=length);
 u32 last=elapsed+31,last_record=last<length||((last&MASK)>=length);
 u32 write=now&MASK,read=(br_start+phase)&MASK;
 if(record!=last_record||write>N-32||read>N-32)return 0;
 for(u32 lane=0;lane<6;lane++)
  if(br_lane_wet[lane]!=(br_excluded&(1u<<lane)?0u:65536u))return 0;
 for(u32 track=0;track<(br_side?12u:6u);track++){
  u32 lane=track<6?track:track-6;
  if(track>=6&&!((u32 *)br_side_on)[lane])continue;
  i32 *channel=(i32 *)((track<6?0x80001858:br_side)+128*lane);
  i16 *history=br_history+N*track;
  if(!(br_excluded&(1u<<lane)))rr_native_plain(channel,history+write,history+read,record);
  else if(record)for(u32 i=0;i<32;i++){
   i32 q=channel[i]>>15;if(q>32767)q=32767;
   if(q< -32767)q=-32767;
   history[write+i]=(i16)q;
  }
 }
 return 1;
}
extern void rr_native_render(u32,i32);
#ifdef RR_FAST_RECORD
/* Sans repeat ni queue de fondu, seule la capture des blocs doit rester. */
static void rr_record(u32 now){
 for(u32 track=0;track<(br_side?12u:6u);track++){
  u32 lane=track,base=0x80001858;
  if(track>=6){lane-=6;if(!((u32*)br_side_on)[lane])continue;base=br_side;}
  const i32 *channel=(const i32*)(base+128*lane);
  i16 *history=br_history+N*track+(now&MASK);
#if RR_RECORD_UNROLL == 2 || RR_RECORD_UNROLL == 4
#define RR_STORE(k) do { i32 q=channel[i+(k)]>>15; if(q>32767)q=32767; if(q< -32767)q=-32767; history[i+(k)]=(i16)q; } while(0)
  for(u32 i=0;i<32;i+=RR_RECORD_UNROLL){
   RR_STORE(0);RR_STORE(1);
#if RR_RECORD_UNROLL == 4
   RR_STORE(2);RR_STORE(3);
#endif
  }
#undef RR_STORE
#else
  for(u32 i=0;i<32;i++){
   i32 q=channel[i]>>15;
#ifdef RR_RECORD_RANGE
   if((u32)(q+32767)>65534u)q=q<0?-32767:32767;
#else
   if(q>32767)q=32767;
   if(q< -32767)q=-32767;
#endif
   history[i]=(i16)q;
  }
#endif
 }
}
#endif
void rr_render(u32 now,i32 target){
#ifdef RR_FAST_RECORD
 if(target<0&&!br_wet){
  if(br_keys!=3){br_valid=0;br_active=-1;return;}
  if(!br_valid){
   u32 fading=0;for(u32 i=0;i<6;i++)fading|=br_lane_wet[i];
   if(!fading){br_active=target;rr_record(now);return;}
  }
 }
#endif
 if(!render_plain_block(now,target))rr_native_render(now,target);
}
#endif
