/* Note115 : rejoindre la phase native une fois, sans toucher au transport A.
 * Les compteurs A sont limites au cycle courant ; B conserve ensuite sa phase.
 * Aucun heap, fichier ou writer MIDI. API reliee a la recette relogee.
 */
typedef unsigned int u32;typedef unsigned char u8;
volatile u32 phase_api[8];
#define V(i) (*(volatile u32 *)phase_api[i])
void phase_join(void){
 if(*(volatile u32 *)0x40a7883c!=1 || !V(0) || !V(1) || V(0)==V(3))return;
 volatile u32 *clock=(volatile u32 *)V(1);if(clock[0])return;
 ((void(*)(void))phase_api[4])();
 volatile u8 *bank=(volatile u8 *)V(2);if(!bank)return;
 u32 now=*(volatile u32 *)0x8000184c,next=*(volatile u32 *)0x40a78628;
 if(!next)return;
 u32 within=now-(next-900000u);if((int)within<0)within=0;if(within>900000u)within=900000u;
 const u32 *durations=(const u32 *)phase_api[5];
 const u32 *ticks=(const u32 *)0x4010afa4;
 for(u32 lane=0;lane<6;lane++){
  u32 speed=*(volatile u8 *)(0x40a788b5+lane),step=*(volatile u8 *)(0x40a7886c+lane),sub=*(volatile u8 *)(0x40a78866+lane);
  u32 len=bank[264*lane+4],bspeed=bank[264*lane+5];
  if(speed>6||step>63||!len||len>64||bspeed>6)return;
  u32 count=ticks[speed];if(!count||count>48||sub>=count)return;
 }
 if(phase_api[6]&&phase_api[7])((void(*)(u32))phase_api[6])(phase_api[7]);
 for(u32 lane=0;lane<6;lane++){
  u32 speed=*(volatile u8 *)(0x40a788b5+lane),step=*(volatile u8 *)(0x40a7886c+lane),sub=*(volatile u8 *)(0x40a78866+lane);
  u32 phase=(step*ticks[speed]+sub)*900000u+within,duration=durations[bank[264*lane+5]],index=phase/duration;
  clock[1+2*lane]=now+duration-phase%duration;
  clock[2+2*lane]=(index+1)%bank[264*lane+4];
 }
 clock[0]=1;
}
