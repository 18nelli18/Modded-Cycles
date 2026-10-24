#include "fx.h"
#ifdef FX_CLOUD
/* CLOUD original : deux tetes Hann, quatre reflexions stereo et trois allpass.
 * Ring de pitch partage avec Shimmer (modes exclusifs). Fenetre et feedback
 * natifs. Aucun malloc ni boucle variable IRQ. Audio Q20, produits Q15.
 */
extern s32 nd_ring[2][8192];
#include "delay_windows.h"
u32 fx_cloud_density=72,fx_cloud_pitch=12;
static const u32 ratios[25]={32768,34716,36781,38968,41285,43740,46341,49097,52016,55109,58386,61858,65536,69433,73562,77936,82570,87480,92682,98193,104032,110218,116772,123715,131072};
static s32 cl_tail[2][4096],cl_ap[2][2048],cl_filter[2][6];
static u32 cl_w,cl_filled,cl_phase,cl_ratio,cl_density,cl_pos[2][3],cl_fill[2][3];
#ifdef FX_CLOUD_REPAIR
/* Raccords cales sur la forme d onde. Recherche courte repartie sur15blocs,
 * meme decalage pour L/R. Ne jamais ajuster une tete encore audible. */
static s32 cl_offset[2],cl_lag,cl_coarse;
static u32 cl_search,cl_head,cl_error,cl_armed,cl_channel;
static s32 point(u32 c,s32 back){return nd_ring[c][(cl_w-(u32)back)&8191]>>12;}
static void align_cloud(void){
 if(cl_filled<5000||cl_ratio==65536)return;
 u32 p=cl_phase>>16,half=p&2047,up=cl_ratio>65536;
 u32 distance=up?2048-half:half,head=up?(p<2048?1:0):(p<2048?0:1);
 if(!cl_armed&&distance<=512&&distance>256){
  cl_armed=1;cl_head=head;cl_search=0;cl_error=0xffffffffu;cl_lag=cl_coarse=0;
  u32 energy[2]={0,0};s32 ref=2591+cl_offset[1-head];
  for(u32 c=0;c<2;c++)for(u32 k=0;k<24;k++){s32 x=point(c,ref-(s32)(8*k));energy[c]+=(u32)(x*x);}
  cl_channel=energy[1]>energy[0]?1:0;
 }
 if(cl_armed==1){
  s32 ref=2591+cl_offset[1-cl_head],next=up?4639:543;
  for(u32 n=0;n<4&&cl_search<58;n++,cl_search++){
   if(cl_search==49)cl_coarse=cl_lag;
   s32 lag=cl_search<49?-192+8*(s32)cl_search:cl_coarse+(s32)cl_search-53;
   u32 error=(u32)(lag<0?-lag:lag);
   for(u32 k=0;k<24;k++){s32 d=point(cl_channel,ref-(s32)(8*k))-point(cl_channel,next+lag-(s32)(8*k));error+=(u32)(d*d);}
   if(error<cl_error){cl_error=error;cl_lag=lag;}
  }
  if(cl_search==58)cl_armed=2;
 }
}
#endif
static s32 mul(s32 x,u32 a){return (x>>15)*(s32)a+(s32)(((u32)x&32767u)*a>>15);}
static s32 limit(s32 x){return x>1048575?1048575:x< -1048576?-1048576:x;}
static s32 read_pitch(u32 c,u32 back){
 u32 d=back>>16,f=(back>>1)&32767;
 s32 a=d>=cl_filled?0:nd_ring[c][(cl_w-d)&8191];
 s32 b=d+1>=cl_filled?0:nd_ring[c][(cl_w-d-1)&8191];
 return a+mul(b-a,f);
}
static s32 read_tail(u32 c,u32 back){return back>=cl_filled?0:cl_tail[c][(cl_w-back)&4095];}
static s32 allpass(s32 x,u32 c){
 for(u32 k=0;k<3;k++){
  u32 len=k==2?97+c*34:k?557+c*42:337+c*36,pos=cl_pos[c][k],at=(k==2?1024:k?400:0)+pos;
  s32 z=cl_fill[c][k]<len?0:cl_ap[c][at];
  if(x>-4&&x<4&&z>-4&&z<4)x=z=0;
  s32 y=z-(x>>1);
  cl_ap[c][at]=x+(y>>1);x=y;
  if(cl_fill[c][k]<len)cl_fill[c][k]++;
  cl_pos[c][k]=pos+1==len?0:pos+1;
 }
 return x;
}
void fx_cloud_reset(void){
 cl_w=cl_filled=cl_phase=0;cl_ratio=65536;
#ifdef FX_CLOUD_REPAIR
 cl_offset[0]=cl_offset[1]=0;cl_armed=0;
#endif
 cl_density=(fx_cloud_density<128?fx_cloud_density:127)*256;
 for(u32 c=0;c<2;c++){
  for(u32 k=0;k<3;k++)cl_pos[c][k]=cl_fill[c][k]=0;
  for(u32 k=0;k<6;k++)cl_filter[c][k]=0;
 }
}
void fx_cloud(s32*io){
 u32 pitch=fx_cloud_pitch<25?fx_cloud_pitch:12,target=ratios[pitch];
 s32 step=((s32)target-(s32)cl_ratio)>>5;
 if(!step&&target!=cl_ratio)step=target>cl_ratio?1:-1;
 cl_ratio=(u32)((s32)cl_ratio+step);
 s32 dstep=((s32)((fx_cloud_density<128?fx_cloud_density:127)*256)-(s32)cl_density)>>5;
 cl_density=(u32)((s32)cl_density+dstep);
 u32 mix=cl_ratio>65536?cl_ratio-65536:65536-cl_ratio;mix=mix>=1024?32768:mix*32;
#ifdef FX_CLOUD_REPAIR
 align_cloud();
#endif
 for(u32 i=0;i<32;i++){
  if(cl_filled<8192)cl_filled++;
  u32 p=cl_phase>>16,wi=p>>4;
  u32 a=ND_HANN[wi]+(((s32)ND_HANN[wi+1]-(s32)ND_HANN[wi])*(s32)(p&15)>>4);
  for(u32 c=0;c<2;c++){
   s32 x=io[2*i+c]>>11,filtered=x;
   for(u32 k=0;k<6;k++){s32 z=filtered+cl_filter[c][k];cl_filter[c][k]=filtered;filtered=z/2;}
   nd_ring[c][cl_w&8191]=cl_ratio>65536?filtered:x;
   s32 wet=x;
   if(mix){
    u32 da=(4127u<<16)-cl_phase,db=(4127u<<16)-((cl_phase+(2048u<<16))&0x0fffffffu);
    #ifdef FX_CLOUD_REPAIR
    da+=((u32)(512+cl_offset[0]))<<16;db+=((u32)(512+cl_offset[1]))<<16;
#endif
    s32 one=read_pitch(c,da),two=read_pitch(c,db),pitched=two+mul(one-two,a);
    wet=x+mul(pitched-x,mix);
   }
   cl_tail[c][cl_w&4095]=wet;
   s32 cluster=(wet+read_tail(c,311+c*48)+read_tail(c,853+c*66)+read_tail(c,1867+c*94))/4;
   s32 diffused=allpass(cluster,c);
   wet+=mul(diffused-wet,cl_density);
   /* Marge de boucle -1,2dB ; feedback natif toujours accessible. */
   io[2*i+c]=limit(wet-(wet>>3))*2048;
  }
  cl_phase=(cl_phase+cl_ratio-65536)&0x0fffffffu;
#ifdef FX_CLOUD_REPAIR
  if(((cl_phase>>16)^p)&2048){
   u32 head=cl_ratio>65536?(p<2048?1:0):(p<2048?0:1);
   if(cl_armed==2&&cl_head==head)cl_offset[head]=cl_lag;
   cl_armed=0;
  }
#endif
  cl_w=(cl_w+1)&8191;
 }
}
#endif
