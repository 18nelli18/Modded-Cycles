/* Armed/latch history capture only. Active repeats and fades use old code. */
typedef unsigned int u32;typedef int s32;typedef short s16;
extern volatile u32 br_keys;
extern u32 br_valid,br_wet,br_lane_wet[6],br_side,br_side_on;
extern s32 br_active;
extern s16 *volatile br_history;
extern void rt_old_render(u32,s32),rt_record_pairs(const s32*,s16*);
void rt_render(u32 now,s32 target){
 if(target<0&&!br_wet&&br_keys==3&&!br_valid&&br_history&&
    !((u32)br_history&3)&&!(now&31)){
  u32 fading=0;for(u32 t=0;t<6;t++)fading|=br_lane_wet[t];
  if(!fading){
   br_active=target;
   for(u32 track=0;track<(br_side?12u:6u);track++){
    u32 lane=track<6?track:track-6;
    if(track>=6&&!((u32 *)br_side_on)[lane])continue;
    const s32*in=(const s32*)((track<6?0x80001858:br_side)+128*lane);
    s16*out=br_history+131072u*track+(now&131071u);
    rt_record_pairs(in,out);
   }
   return;
  }
 }
 rt_old_render(now,target);
}
