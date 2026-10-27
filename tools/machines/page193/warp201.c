/* Horloge virtuelle du sequenceur uniquement ; MIDI/BPM et compteur physique
 * restent natifs. Une subdivision virtuelle dure16/N subdivisions reelles.
 * Le reste entier conserve la precision sur les gammes non divisibles. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
extern u32 pl_length(const u8*),pl_warp(const u8*);
extern u32 wp_old_insert(u32,u32),wp_old_schedule(u32,u32,u32),wp_old_cancel(u32,u32,u32);
static u32 valid,next_due,remainder,pattern,ratio,last_now;
static volatile u32 active;
static u32 frame_ipl,frame_now,frame_exact,frame_ratio;
#ifdef PAGE_TRACK201
extern u32 pt_length(const u8*,u32),pt_warp(const u8*,u32);
struct track_clock {u32 valid,next,rest,ratio,last,exact;};
static struct track_clock clocks[6];static u32 track_frame,due_mask;
static void track_advance(struct track_clock*c,u32 n){c->next+=14400000u/n;c->rest+=14400000u%n;if(c->rest>=n){c->next++;c->rest-=n;}}
#endif
static u32 sr_ipl(void){u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));return sr&0x700;}
static u32 get_pattern(void){return *(volatile u32*)0x40a7887c;}
static u32 get_ratio(u32 p){return p&&pl_warp((const u8*)p+30642)?pl_length((const u8*)p+30642):16;}
static u32 running(void){return !*(volatile u32*)0x40a78630&&(*(volatile u32*)0x40a7883c==1||*(volatile u32*)0x40a78874==1);}
static void advance(u32 n){u32 q=14400000u/n,r=14400000u%n;next_due+=q;remainder+=r;if(remainder>=n){next_due++;remainder-=n;}}
u32 wp_begin(void){
 /* Les sous-ticks natifs occupes ne sont pas un arret du transport. */
 active=0;if(*(volatile u32*)0x40a78630)return 1;u32 p=get_pattern(),n=get_ratio(p),now=*(volatile u32*)0x40a78628;
#ifdef PAGE_TRACK201
 if(p&&*((const u8*)p+30667)==1){
  valid=0;track_frame=1;due_mask=0;
  if(!running()){for(u32 t=0;t<6;t++)clocks[t].valid=0;return 1;}
  frame_now=now;frame_ipl=sr_ipl();
  for(u32 t=0;t<6;t++){
   struct track_clock*c=clocks+t;const u8*h=(const u8*)p+30642;
   u32 rate=pt_warp(h,t)?pt_length(h,t):16;
   if(!c->valid||c->ratio!=rate||(s32)(now-c->last)<0||now-c->last>1800000u){c->valid=1;c->next=now;c->rest=0;c->ratio=rate;}
   c->last=now;if((s32)(now-c->next)>=0){c->exact=c->next;track_advance(c,rate);due_mask|=1u<<t;}
  }
  active=1;return 1;
 }
 if(track_frame){for(u32 t=0;t<6;t++)clocks[t].valid=0;track_frame=0;}
#endif
 if(!running()||n==16){valid=0;return 1;}
 if(!valid||ratio!=n||(s32)(now-last_now)<0||now-last_now>1800000u){valid=1;pattern=p;ratio=n;remainder=0;next_due=now;}
 pattern=p;last_now=now;
 if((s32)(now-next_due)<0)return 0;
 frame_now=now;frame_exact=next_due;frame_ratio=n;frame_ipl=sr_ipl();advance(n);active=1;return 1;
}
static void observe(void){
 u32 p=get_pattern(),n=get_ratio(p);
 pattern=p;
 if(n!=frame_ratio){ratio=n;frame_ratio=n;remainder=0;next_due=frame_exact;advance(n);if(n==16)valid=0;}
}
void wp_finish(void){if(active){
#ifdef PAGE_TRACK201
 if(!track_frame)
#endif
 observe();active=0;}}
u32 wp_time(u32 timestamp){
 if(!active||sr_ipl()!=frame_ipl)return timestamp;
 observe();s32 delta=(s32)(timestamp-frame_now),n=frame_ratio;
 /* Quotient/reste evite un produit intermediaire signe debordant. */
 s32 scaled=(delta/n)*16+((delta%n)*16)/n;
 return frame_exact+(u32)scaled;
}
#ifdef PAGE_TRACK201
u32 wp_track_due(u32 t){return !active||!track_frame||t>=6||(due_mask&(1u<<t));}
u32 wp_track_time(u32 timestamp,u32 t){
 if(!active||sr_ipl()!=frame_ipl)return timestamp;
 if(!track_frame)return wp_time(timestamp);
 if(t>=6||!(due_mask&(1u<<t)))return timestamp;
 s32 delta=(s32)(timestamp-frame_now),n=clocks[t].ratio;
 return clocks[t].exact+(u32)((delta/n)*16+((delta%n)*16)/n);
}
u32 wp_insert(u32 event,u32 timestamp){
 if(track_frame){if(event&&!*(const u32*)event)timestamp=wp_track_time(timestamp,*(const u32*)(event+8));}
 else timestamp=wp_time(timestamp);
 return wp_old_insert(event,timestamp);
}
#else
u32 wp_insert(u32 event,u32 timestamp){return wp_old_insert(event,wp_time(timestamp));}
#endif
u32 wp_schedule(u32 timestamp,u32 fn,u32 track){
#ifdef PAGE_TRACK201
 if(track_frame)timestamp=fn==0x40054140?wp_track_time(timestamp,track):timestamp;else
#endif
 timestamp=wp_time(timestamp);return wp_old_schedule(timestamp,fn,track);
}
u32 wp_cancel(u32 timestamp,u32 fn,u32 track){
#ifdef PAGE_TRACK201
 if(track_frame)timestamp=fn==0x40054140?wp_track_time(timestamp,track):timestamp;else
#endif
 timestamp=wp_time(timestamp);return wp_old_cancel(timestamp,fn,track);
}
