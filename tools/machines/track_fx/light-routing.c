/* Prototype prive : reverbe/delay existants partages, modulation par type.
 * Entrees stereo Q31, gains stereo Q15, sommes intermediaires Q20 bornees.
 * Un etat par type, partage par toutes les pistes envoyees vers ce type.
 * Les queues finies sont retirees ; aucun noyau ne tourne sans demande.
 */
typedef unsigned int u32;typedef signed int s32;typedef short s16;
extern void lt_ch1(s32*,const s32*,const s16*,u32,u32),lt_ch2(s32*,const s32*,const s16*,u32,u32);
extern void lt_ring(s32*,const s32*),lt_phaser(s32*,const s32*),lt_crush(s32*,const s32*,u32,u32),lt_crush2(s32*,const s32*,u32,u32);
#ifndef MF_NO_VINYL
extern void lt_vinyl(s32*,const s32*);
#else
u32 lt_dust_target[2];
#endif
extern u32 lt_dust_target[2];
u32 lt_crackle=24,lt_warble=24,lt_wspeed=32,lt_ring_freq=80,lt_ring_depth=127,lt_phase_rate=48,lt_phase_depth=112,lt_phase_feedback=64;
u32 lt_config[8][4]={{0},{42,64},{42,64},{24,24,32},{80,127},{48,112,64},{96,12}};
s32 lt_bus[8][64];static s32 work[64];
u32 lt_active,lt_calls[8],lt_sent;
static u32 drained[8],quiet[8];
static s32 native_gain[8][2][6];
static s32 sat20(s32 x){return x>1048575?1048575:x< -1048576?-1048576:x;}
void lt_render(s32*out){
 for(u32 i=0;i<64;i++)out[i]=0;
 /* Aucun effet actif : le tampon nul est deja le resultat final. */
 if(!lt_active)return;
 for(u32 e=1;e<8;e++)if(lt_active&(1u<<e)){
  const s32*in=lt_bus[e];const u32*p=lt_config[e==7?6:e];s16 cp[2]={(s16)(p[0]*256),(s16)(p[1]*256)};lt_calls[e]++;
  switch(e){
   case 1:lt_ch1(work,in,cp,1,256);break;
   case 2:lt_ch2(work,in,cp,2,256);break;
#ifndef MF_NO_VINYL
   case 3:lt_crackle=p[0];lt_warble=p[1];lt_wspeed=p[2];lt_vinyl(work,in);break;
#endif
   case 4:lt_ring_freq=p[0];lt_ring_depth=p[1];lt_ring(work,in);break;
   case 5:lt_phase_rate=p[0];lt_phase_depth=p[1];lt_phase_feedback=p[2];lt_phaser(work,in);break;
   case 6:lt_crush(work,in,p[0],p[1]);break;
   case 7:lt_crush2(work,in,p[0],p[1]);break;
   default:continue;
  }
  /* A send actif, aucun balayage de silence n'est necessaire. */
  if(lt_sent&(1u<<e)){
   if(e==3||e==7){for(u32 i=0;i<64;i++)out[i]+=(work[i]>>11)-(in[i]>>11);}
   else {for(u32 i=0;i<64;i++)out[i]+=work[i]>>11;}
   drained[e]=quiet[e]=0;
  }
  else{
   /* Accumuler et tester le silence dans le meme parcours, sans changer
    * les noyaux, les arrondis ou les compteurs de fin de queue. */
   u32 input=0,output=0;
   if(e==3||e==7){for(u32 i=0;i<64;i++){s32 w=work[i],v=in[i];out[i]+=(w>>11)-(v>>11);input|=(u32)v;output|=(u32)w;}}
   else {for(u32 i=0;i<64;i++){s32 w=work[i];out[i]+=w>>11;input|=(u32)in[i];output|=(u32)w;}}
   if(input){drained[e]=quiet[e]=0;}
   else{if(drained[e]<1024)drained[e]++;quiet[e]=output?0:quiet[e]<1024?quiet[e]+1:1024;
    u32 hold=e==5?128:(e==1||e==2||e==3)?64:1;if(drained[e]>=hold&&quiet[e]>=8)lt_active&=~(1u<<e);
   }
  }
 }
 for(u32 i=0;i<64;i++)out[i]=sat20(out[i])*2048;
}
extern void lt_sum1(s32*,const s32*,s32*,const s32*);
/* Garder aussi les sources dont l'ancien gain doit finir sa rampe. */
u32 lt_source_mask(u32 wanted){
 for(u32 e=1;e<8&&wanted!=63;e++)if(lt_active&(1u<<e))
  for(u32 t=0;t<6;t++)if(!(wanted&(1u<<t))&&(native_gain[e][0][t]||native_gain[e][1][t]))wanted|=1u<<t;
 return wanted;
}
void lt_build_slots(const s32*left,const s32*right,const unsigned char*route,const u32*send,u32 enabled){
 u32 mask=lt_active;unsigned char selected[12];lt_sent=0;lt_dust_target[0]=lt_dust_target[1]=0;
#ifdef MF_NO_VINYL
 mask&=~8u;
#endif
 for(u32 t=0;t<12;t++){u32 e=route[t];selected[t]=(enabled&(1u<<(t%6)))&&e>0&&e<8
#ifdef MF_NO_VINYL
 &&e!=3
#endif
 &&(send[2*t]||send[2*t+1])?e:0;if(selected[t]){mask|=1u<<selected[t];lt_sent|=1u<<selected[t];}}
 lt_active=mask;
 for(u32 e=1;e<8;e++)if(mask&(1u<<e)){
  s32 delta[2][6];u32 used[2]={0,0},same=left==right,n[2]={0,0},single[2]={0,0};
  u32 bank=e>=5?6:0;
  for(u32 t=0;t<6;t++)for(u32 c=0;c<2;c++){
   u32 amount=selected[bank+t]==e?(send[2*bank+2*t+c]>32768?32768:send[2*bank+2*t+c]):0;
   if(e==3&&amount>lt_dust_target[c])lt_dust_target[c]=amount;
   s32 old=native_gain[e][c][t],target=(s32)(0u-(amount<<16));
   delta[c][t]=old==(s32)0x80000000u&&!target?67108864:(s32)((u32)target-(u32)old)>>5;
   used[c]|=(u32)old|(u32)target;if(old||target){n[c]++;single[c]=t;}
   if(c&&((u32)native_gain[e][0][t]!=(u32)old||delta[0][t]!=delta[1][t]))same=0;
  }
  for(u32 c=0;c<2;c++){
   s32*out=lt_bus[e]+c;
   if(c&&same){for(u32 i=0;i<32;i++)out[2*i]=out[2*i-1];for(u32 t=0;t<6;t++)native_gain[e][1][t]=native_gain[e][0][t];}
   else if(n[c]==1){u32 t=single[c];lt_sum1(out,(c?right:left)+32*t,&native_gain[e][c][t],&delta[c][t]);}
   else if(used[c])((void(*)(s32*,const s32*,s32*,const s32*))0x40056716)(out,c?right:left,native_gain[e][c],delta[c]);
   else for(u32 i=0;i<32;i++)out[2*i]=0;
  }
 }
}
u32 lt_run_slots(const s32*l,const s32*r,const unsigned char*route,const u32*send,u32 enabled,s32*out){if(!lt_active){u32 used=0;for(u32 t=0;t<12;t++)if((enabled&(1u<<(t%6)))&&route[t]>0&&route[t]<8&&(send[2*t]||send[2*t+1]))used=1;if(!used)return 0;}lt_build_slots(l,r,route,send,enabled);lt_render(out);return 1;}
