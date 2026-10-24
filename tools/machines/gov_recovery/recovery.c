/* Reprise apres vol de voix ; seul le bloc de reprise execute ce C.
 * Le chemin ordinaire et le suivi restent dans les stubs SRAM natifs.
 */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
s32 gr_last[6];
static s32 blend(s32 x,s32 y,u32 gain){
 u32 other=65536-gain;
 s32 hi=(x>>16)*(s32)gain+(y>>16)*(s32)other;
 u32 lo=((u32)x&65535)*gain+((u32)y&65535)*other;
 return hi+(s32)(lo>>16);
}
void gr_recover(u32 lane,s32 *buffer){
 s32 last=gr_last[lane];u32 gain=0;
 for(u32 i=0;i<31;i++,gain+=2114)buffer[i]=blend(buffer[i],last,gain);
 ((volatile u8*)0x46732046)[lane]=0;
}
/* Diagnostic prive A/P/O/N ; aucun changement des compteurs DX originaux. */
extern volatile u32 dx_enabled,dx_peak,dx_over,dx_new;
extern volatile u32 dx_beat_api[3];
extern void gr_dx_before_original(u32);
u32 gr_diag_sum,gr_diag_blocks;
void gr_dx_before(u32 now){
 gr_dx_before_original(now);
 if(dx_enabled&&*(volatile u32*)0x40a7883c==1){
  u32 elapsed=now-*(volatile u32*)0x46732080;
  u32 load=elapsed>901120?2560:elapsed*256/90112;
  if(gr_diag_blocks<1000000){gr_diag_sum+=load;gr_diag_blocks++;}
 }
}
u32 gr_beat_key(const u32 *event){
 u32 before=*(volatile u32*)dx_beat_api[1];
 u32 result=((u32(*)(const u32*))dx_beat_api[0])(event);
 if(dx_enabled&&before==3&&*(volatile u32*)dx_beat_api[1]!=3){
  char text[40];u32 average=gr_diag_blocks?(gr_diag_sum/gr_diag_blocks)*100/256:0;
  ((u32(*)())0x40000e6e)(text,"A%u P%u O%u N%u",average,dx_peak/901,dx_over,dx_new);
  ((void(*)(const char*))dx_beat_api[2])(text);
  dx_peak=dx_over=dx_new=gr_diag_sum=gr_diag_blocks=0;
 }
 return result;
}
