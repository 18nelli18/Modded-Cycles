/* ECO rate cap for Macro's existing pitch-safe LITE/RATE models only.
 * Uses original voice storage and renderer; other models retain native timing. */
#include "braids/macro_oscillator.h"
typedef unsigned int u32;typedef int s32;typedef short s16;
struct EcoTrack{
 braids::MacroOscillator osc;s16 x[22+64+16];
 s32 fill,rd,mode,want;u32 src,hold;s32 size,bits;u32 ph,hph;s32 cur;
};
static_assert(sizeof(EcoTrack)==17232,"Pinned Macro Track ABI changed");
extern "C" unsigned char eco_macro_store[];
extern "C" void mf_old_eco_macro_update(s32,char*,const char*);
static const s16 headroom[47]={0,-1,0,-1,-1,0,0,-1,-1,3072,3072,3072,3072,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,0,0,2437,-1,-1,-1,-1,-1,0};
static const u32 steps[65]={16777216,16138581,15524256,14933316,14364871,13818063,13292070,12786100,12299389,11831206,11380844,10947625,10530897,10130032,9744426,9373499,9016691,8673465,8343305,8025712,7720208,7426334,7143646,6871719,6610143,6358524,6116483,5883655,5659690,5444251,5237012,5037662,4845900,4661438,4483998,4313312,4149123,3991184,3839257,3693114,3552533,3417304,3287222,3162092,3041725,2925940,2814562,2707424,2604365,2505228,2409865,2318132,2229891,2145009,2063358,1984815,1909262,1836584,1766674,1699424,1634735,1572507,1512649,1455069,1399681};
extern "C" void eco_macro_update(s32 pmod,char*v,const char*p){
 mf_old_eco_macro_update(pmod,v,p);
 u32 lane=((u32)v-0x42308828u)/0x31c;if(lane>=6)return;
 s32 shape=*(const s16*)(p+0x18)>>8;if(shape<0)shape=0;if(shape>46)shape=46;
 s32 head=headroom[shape];if(head<0)return;
 s32 fine=(*(const s16*)(p+0x22)+128)>>8;if(fine<0)fine=0;if(fine>127)fine=127;
 s32 rate=fine<64?64-fine:0;if(rate>=18)return;rate=18;
 s32 note=(s32)*(const s16*)(p+0x14)*256-(64<<16)+pmod;
 if(note<0)note=0;if(note>(127<<16))note=127<<16;note>>=9;
 s32 d=16383-1536-head-note;if(d<0)return;d/=86;if(d>rate)d=rate;
 EcoTrack*tr=(EcoTrack*)(eco_macro_store+lane*sizeof(EcoTrack));
 tr->want=1;tr->src=steps[d];tr->size=2*((6*(s32)(steps[d]>>8)+(1<<15))>>16);if(tr->size<2)tr->size=2;
 tr->osc.set_pitch(note+1536+86*d);tr->hold=d==rate?(1u<<24):steps[rate];
}
