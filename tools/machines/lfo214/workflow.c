/* Page LFO secondaire : seuls navigation/fermeture/clic restent locaux.
 * Les gestes musicaux traversent la vraie chaine de vues, flags intacts. */
typedef unsigned int u32;
#define N(a) ((u32(*)())(a))
extern u32 wf_old_key(u32,const u32*),wf_old_encoder(u32,const u32*);
extern void wf_old_new(u32),wf_old_decode_end(u32,const unsigned char*,u32);
volatile u32 wf_generation;
static u32 trig_held(void){if(N(0x4007faf4)(8))return 0;for(u32 key=16;key<32;key++)if(N(0x4007faf4)(key))return 1;return 0;}
u32 wf_key(u32 view,const u32*e){
 if(!e)return 0;u32 code=e[3];if(code==32&&trig_held())return 0;
 if(code==8||code==12||code==13||code==32)return wf_old_key(view,e);
 return 0;
}
u32 wf_encoder(u32 view,const u32*e){if(trig_held())return 0;return wf_old_encoder(view,e);}
static void changed(u32 raw){u32 project=*(volatile u32*)0x40fe4228;if(project&&*(volatile u32*)(project+16)==raw)wf_generation++;}
void wf_new(u32 raw){changed(raw);wf_old_new(raw);}
void wf_decode_end(u32 raw,const unsigned char*in,u32 ok){if(ok)changed(raw);wf_old_decode_end(raw,in,ok);}
