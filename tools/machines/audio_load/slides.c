/* Note 112 : court-circuit exact du balayage CC sans slide active. */
typedef unsigned int u32;
volatile u32 ao_api[6];
extern void ao_tick_original(void);
void ao_tick(void){
 u32 clock=*(volatile u32 *)ao_api[0],pattern=*(volatile u32 *)ao_api[1];
 if(!clock||*(volatile u32 *)clock!=1||!pattern||*(volatile u32 *)ao_api[2]!=pattern){ao_tick_original();return;}
 u32 rate=*(volatile u32 *)ao_api[3]+1;
 if(rate<3){*(volatile u32 *)ao_api[3]=rate;return;}
 if(*(volatile u32 *)ao_api[4]>71){ao_tick_original();return;}
 for(u32 lane=0;lane<6;lane++){
  volatile u32 *state=(volatile u32 *)(ao_api[5]+64*lane);
  if(state[0]==pattern&&(state[3]&4095)){ao_tick_original();return;}
 }
 *(volatile u32 *)ao_api[3]=0;
}
