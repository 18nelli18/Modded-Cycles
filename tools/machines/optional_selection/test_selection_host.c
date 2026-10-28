/* Exhaustivite du selecteur pour les 524288 combinaisons, sans materiel. */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
volatile unsigned int opt_mask,machine_valid,machine_stamp,machine_result;
extern unsigned int opt_step(unsigned int,int),opt_enabled(unsigned int);
static const unsigned int order[25]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,21,22,23,24,17};
int main(void){
 unsigned long long checks=0;
 for(unsigned int mask=0;mask<524288;mask++){
  opt_mask=mask;unsigned int list[25],n=0;
  for(unsigned int i=0;i<25;i++)if(order[i]<6||(mask&(1u<<(order[i]-6))))list[n++]=order[i];
  for(unsigned int i=0;i<n;i++){
   if(!opt_enabled(list[i])||opt_step(list[i],1)!=list[i+1<n?i+1:i]||opt_step(list[i],-999)!=list[i?i-1:0]||opt_step(list[i],0)!=list[i]){fprintf(stderr,"FAIL mask%u id%u\n",mask,list[i]);return 1;}
   checks+=4;
  }
  for(unsigned int id=6;id<27;id++)if(id>=25||!(mask&(1u<<(id-6)))){
   if(opt_enabled(id)||opt_step(id,0)!=0||opt_step(id,1)!=1||opt_step(id,-1)!=0)return 2;
   checks+=4;
  }
 }
 printf("PASS 524288 masks: stock-six always present, optional IDs stable, MIDI last, both bounds, accelerated deltas, stale/invalid ID normalization; %llu checks\n",checks);
 return 0;
}
