/* Dummy28 : controles UI uniquement. Le rendu est court-circuite en assembleur.
 * Les reglages globaux de transport restent ceux de l OS. Aucun heap DSP. */
typedef unsigned int u32;typedef unsigned short u16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#ifdef DY_REMOVE
extern volatile u32 dy_md_present;
#else
volatile u32 dy_md_present;
#endif
extern const u8 dy_order[];extern const u32 dy_count;
extern u32 dy_old_set(u32,u32,u32,u32);
u32 dy_allowed(u32 m){
 if(m<6)return 1;
#if DY_FULL
#if DY_OPTIONAL
 u32 md=dy_md_present,mask=md?*(volatile u32*)0x469c423c:*(volatile u32*)0x468d0ff0;if(!md&&!mask)mask=0x7ffff;
#ifdef DY_REMOVE
 return m<28&&((mask>>(m-6))&1);
#else
 return m<=28&&((mask>>(m-6))&1);
#endif
#else
 return m<=24&&m!=21;
#endif
#else
 return 0;
#endif
}
u32 dy_set(u32 object,u32 machine,u32 flags,u32 mode){
 u32 r=dy_old_set(object,machine,flags,mode);
#ifndef DY_REMOVE
 if(machine==28&&object){u32 vt=*(const u32*)object;if(vt){u32 get=*(const u32*)(vt+40);u8*raw=get?(u8*)N(get)(object):0;if(raw&&raw[38]==28){u32 records[18];for(u32 i=0;i<9;i++){records[2*i]=10+i;records[2*i+1]=0;}u32 pair[2]={(u32)records,(u32)(records+18)};N(0x4001416c)(object,pair);}}}
#endif
 return r;
}
void dy_draw_marks(u32 canvas,u32 selected){u32 n=0;for(u32 i=0;i<dy_count;i++){u32 id=dy_order[i];if(!dy_allowed(id))continue;u32 x=68+5*(n%13),y=9+4*(n/13);N(id==selected?0x40070efc:0x40070c4e)(canvas,x-4,y,x,y+3,1);n++;}}
