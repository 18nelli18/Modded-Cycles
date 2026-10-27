/* Horloge virtuelle du sequenceur uniquement ; MIDI/BPM et compteur physique
 * restent natifs. Une subdivision virtuelle dure16/N subdivisions reelles.
 * Le reste entier conserve la precision sur les gammes non divisibles. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
extern u32 pl_length(const u8*),pl_warp(const u8*);
extern u32 wp_old_insert(u32,u32),wp_old_schedule(u32,u32,u32),wp_old_cancel(u32,u32,u32);
static u32 valid,next_due,remainder,pattern,ratio,last_now;
static volatile u32 active;
static u32 frame_ipl,frame_now,frame_exact,frame_ratio;
static u32 sr_ipl(void){u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));return sr&0x700;}
static u32 get_pattern(void){return *(volatile u32*)0x40a7887c;}
static u32 get_ratio(u32 p){return p&&pl_warp((const u8*)p+30642)?pl_length((const u8*)p+30642):16;}
static u32 running(void){return !*(volatile u32*)0x40a78630&&(*(volatile u32*)0x40a7883c==1||*(volatile u32*)0x40a78874==1);}
static void advance(u32 n){u32 q=14400000u/n,r=14400000u%n;next_due+=q;remainder+=r;if(remainder>=n){next_due++;remainder-=n;}}
u32 wp_begin(void){
 /* Les sous-ticks natifs occupes ne sont pas un arret du transport. */
 active=0;if(*(volatile u32*)0x40a78630)return 1;u32 p=get_pattern(),n=get_ratio(p),now=*(volatile u32*)0x40a78628;
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
void wp_finish(void){if(active){observe();active=0;}}
u32 wp_time(u32 timestamp){
 if(!active||sr_ipl()!=frame_ipl)return timestamp;
 observe();s32 delta=(s32)(timestamp-frame_now),n=frame_ratio;
 /* Quotient/reste evite un produit intermediaire signe debordant. */
 s32 scaled=(delta/n)*16+((delta%n)*16)/n;
 return frame_exact+(u32)scaled;
}
u32 wp_insert(u32 event,u32 timestamp){return wp_old_insert(event,wp_time(timestamp));}
u32 wp_schedule(u32 timestamp,u32 fn,u32 track){return wp_old_schedule(wp_time(timestamp),fn,track);}
u32 wp_cancel(u32 timestamp,u32 fn,u32 track){return wp_old_cancel(wp_time(timestamp),fn,track);}

