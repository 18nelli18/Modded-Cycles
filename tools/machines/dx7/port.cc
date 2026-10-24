/*
 * Copyright 2016-2025 Pascal Gauthier.
 * Copyright 2012 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* Port ColdFire de MSFA/Dexed ; voir NOTICE et sources Apache dans upstream/.
 * Toutes les donnees de voix sont fixes et privees a une piste, sans heap. */
#include "core/synth.h"
#include "core/env.h"
#include "core/pitchenv.h"
#include "core/lfo.h"
#include "core/fm_core.h"
#include "core/freqlut.h"
#ifdef DX7_BANK_GUARD
#include "core/exp2.h"
#endif
typedef uint32_t u32;typedef int32_t s32;typedef uint8_t u8;
extern const int32_t dx7_fine[100],dx7_detune[1920],dx7_ampmod[513],dx7_time[128];
extern "C" const u8 *dx7_patch(u32);
static int clamp(int x,int a,int b){return x<a?a:x>b?b:x;}
struct DxTrack{
 Env env[6];PitchEnv pitch;Lfo lfo;FmCore core;FmOpParams op[6];
 s32 base[6],feedback[2],note16;u32 bright,time,fb,active,held;
 u8 patch[156];
#ifdef DX7_OPT
 s32 cached_pitch;u32 frequency_valid;
#ifdef DX7_BANK_GUARD
 u32 volume_shift;
#endif
#endif
};
static DxTrack dx7_tracks[6];
extern "C" const u32 dx7_track_bytes=sizeof(DxTrack);
/* Ces tables/calibrations proviennent de dx7note.cc (Apache2.0), Google et
 * Pascal Gauthier ; version originale conservee dans upstream/. */
static const s32 coarse_mul[32]={-16777216,0,16777216,26591258,33554432,38955489,43368474,47099600,50331648,53182516,55732705,58039632,60145690,62083076,63876816,65546747,67108864,68576247,69959732,71268397,72509921,73690858,74816848,75892776,76922906,77910978,78860292,79773775,80654032,81503396,82323963,83117622};
static const u8 velocity_data[64]={0,70,86,97,106,114,121,126,132,138,142,148,152,156,160,163,166,170,173,174,178,181,184,186,189,190,194,196,198,200,202,205,206,209,211,214,216,218,220,222,224,225,227,229,230,232,233,235,237,238,240,241,242,243,244,246,246,248,249,250,251,252,253,254};
static const u8 exp_scale[33]={0,1,2,3,4,5,6,7,8,9,11,14,16,19,23,27,33,39,47,56,66,80,94,110,126,142,158,174,190,206,222,238,250};
static const u8 pitch_sens[8]={0,10,20,33,55,92,153,255};
static const u32 amp_sens[4]={0,4342338,7171437,16777216};
static int curve(int g,int d,int c){int s=c==0||c==3?(g*d*329)>>12:(exp_scale[min(g,32)]*d*329)>>15;return c<2?-s:s;}
static int scale_level(int n,const u8*p){int x=n-p[8]-17;return x>=0?curve((x+1)/3,p[10],p[12]):curve(-(x-1)/3,p[9],p[11]);}
static s32 frequency(int n,const u8*p){
 if(p[17])return (4458616*((p[18]&3)*100+p[19])>>3)+(p[20]>7?13457*(p[20]-7):0);
 return 50857777+1398101*n+dx7_detune[n*15+p[20]]+coarse_mul[p[18]]+dx7_fine[p[19]];
}
extern "C" void dx7_note_on(u32 lane,const u8 *patch,s32 note16,u32 velocity){
 if(lane>=6)return;DxTrack&t=dx7_tracks[lane];int n=clamp((note16>>16)+(int)patch[144]-24,0,127),r[4],l[4];
 for(int i=0;i<156;i++)t.patch[i]=patch[i];t.note16=note16;t.active=t.held=1;t.feedback[0]=t.feedback[1]=0;
#ifdef DX7_BANK_GUARD
 u32 carrier_peak=0;t.volume_shift=0;
#endif
 for(int k=0;k<6;k++){
  const u8*p=patch+21*k;
  for(int i=0;i<4;i++){r[i]=p[i];l[i]=p[4+i];}
  int ol=min(127,Env::scaleoutlevel(p[16])+scale_level(n,p))*32;
  ol+=((p[15]*(velocity_data[clamp(velocity,0,127)>>1]-239)+7)>>3)*16;
  t.env[k].init(r,l,max(0,ol),(p[13]*clamp(n/3-7,0,31))>>3);
#ifdef DX7_BANK_GUARD
  /* Gain choisi au trig, a velocite de reference100 : les velocites douces
   * gardent leur dynamique. Ne toucher ni le patch ni la modulation FM. */
  if(FmCore::isCarrier(patch[134],k)&&(patch[155]&(1u<<k))){
   int peak=0;for(int j=0;j<4;j++)peak=max(peak,l[j]);
   int ref=min(127,Env::scaleoutlevel(p[16])+scale_level(n,p))*32;
   ref+=((p[15]*(velocity_data[50]-239)+7)>>3)*16;
   int target=clamp(((Env::scaleoutlevel(peak)>>1)<<6)+max(0,ref)-4256,16,17<<8);
   carrier_peak+=(u32)Exp2::lookup((target<<16)-(14<<24));
  }
#endif
  t.op[k].gain_out=0;if(patch[136])t.op[k].phase=0;
  t.base[k]=frequency(n,p);
 }
 for(int i=0;i<4;i++){r[i]=patch[126+i];l[i]=patch[130+i];}t.pitch.set(r,l);
 t.lfo.reset(patch+137);t.lfo.keydown();
#ifdef DX7_BANK_GUARD
 /* Rattraper jusqu a36dB, seulement si les carriers sont faibles. Constant
  * pendant toute la note, aucun gain dependant du niveau instantane. */
 while(carrier_peak&&carrier_peak<(1u<<23)&&t.volume_shift<6){carrier_peak<<=1;t.volume_shift++;}
#endif
#ifdef DX7_OPT
 t.frequency_valid=0;
#endif
}
extern "C" void dx7_controls(u32 lane,s32 note16,u32 bright,u32 time,u32 feedback,u32 held){
 if(lane>=6)return;DxTrack&t=dx7_tracks[lane];
 #ifdef DX7_OPT
 if(note16!=t.note16){
#endif
 int delta=(s32)((int64_t)(note16-t.note16)*1398101>>16);t.note16=note16;
 for(int k=0;k<6;k++)if(!t.patch[k*21+17])t.base[k]+=delta;
#ifdef DX7_OPT
 t.frequency_valid=0;}
#endif
 t.bright=bright&127;t.time=time&127;t.fb=feedback&127;
 if(t.held&&!held){for(int k=0;k<6;k++)t.env[k].keydown(false);t.pitch.keydown(false);}t.held=held;
}
extern "C" u32 dx7_is_active(u32 lane){
 if(lane>=6)return 0;DxTrack&t=dx7_tracks[lane];if(!t.active)return 0;
 for(int k=0;k<6;k++)if(FmCore::isCarrier(t.patch[134],k)&&t.env[k].isActive())return 1;
 return t.active=0;
}
extern "C" void dx7_block_c(u32 lane,s32*out){
 for(int i=0;i<32;i++)out[i]=0;if(lane>=6||!dx7_is_active(lane))return;DxTrack&t=dx7_tracks[lane];const u8*p=t.patch;
 s32 lv=t.lfo.getsample(),ld=t.lfo.getdelay();u32 pmd=((u32)p[139]*165>>6)*(u32)ld;
 s32 sens=(s32)pitch_sens[p[143]&7]*(lv-(1<<23));s32 pitch=t.pitch.getsample();
#ifdef DX7_OPT
 if(pmd&&sens)
#endif
 pitch+=(s32)(((int64_t)pmd*sens)>>39);
 u32 amod=(u32)(((uint64_t)((u32)p[140]*165>>6)*(u32)ld)>>8);
 #ifdef DX7_OPT
 if(amod)
#endif
 amod=(u32)(((uint64_t)amod*((1<<24)-lv))>>24);
 for(int k=0;k<6;k++){
  #ifdef DX7_OPT
  if(!t.frequency_valid||t.cached_pitch!=pitch)
#endif
  t.op[k].freq=Freqlut::lookup(t.base[k]+(p[21*k+17]?0:pitch));
  t.env[k].setSpeed(dx7_time[t.time]);s32 level=t.env[k].getsample();
  if(!FmCore::isCarrier(p[134],k))level=clamp(level+((s32)t.bright-64)*1048576,0,17<<24);
  u32 a=0;
#ifdef DX7_OPT
  if(amod&&p[21*k+14])
#endif
  a=(u32)(((uint64_t)amod*amp_sens[p[21*k+14]&3])>>24);
  if(a){u32 index=a>>15;if(index>512)index=512;u32 pt=dx7_ampmod[index];
   if(index<512)pt+=((dx7_ampmod[index+1]-pt)*(a&32767))>>15;
   level-=(s32)(((int64_t)level*pt)>>24);
  }
  t.op[k].level_in=(p[155]&(1u<<k))?clamp(level,0,17<<24):0;
 }
 #ifdef DX7_OPT
 t.frequency_valid=1;t.cached_pitch=pitch;
#endif
 int fb=clamp(p[135]+((s32)t.fb-64)/9,0,7);t.core.render(out,t.op,p[134],t.feedback,fb?8-fb:16);
 /* Q24 -> Q31 ; reserve de niveau pour plusieurs carriers, saturation explicite. */
 #ifdef DX7_BANK_GUARD
 int limit=134217727>>t.volume_shift,scale=16<<t.volume_shift;
 for(int i=0;i<32;i++)out[i]=clamp(out[i],-limit,limit)*scale;
#else
 for(int i=0;i<32;i++)out[i]=clamp(out[i],-134217727,134217727)*16;
#endif
}
