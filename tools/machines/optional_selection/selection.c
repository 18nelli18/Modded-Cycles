/* Selection bornee, IDs stables. Le runtime commun conserve ses adresses. */
typedef unsigned int u32;typedef signed int s32;
extern const volatile u32 opt_mask;
extern volatile u32 machine_valid,machine_stamp,machine_result;
static const unsigned char order[25]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,21,22,23,24,17};
const char opt_unavailable[]="UNAVAILABLE";
u32 opt_enabled(u32 m){return m<6||(m<25&&((opt_mask>>(m-6))&1));}
u32 opt_step(u32 m,s32 delta){
 if(!opt_enabled(m))m=0;if(!delta)return m;u32 at=0;while(at<25&&order[at]!=m)at++;
 for(s32 i=(s32)at+(delta>0?1:-1);i>=0&&i<25;i+=delta>0?1:-1)if(opt_enabled(order[i]))return order[i];return m;
}
u32 opt_fx_step(u32 m,s32 delta){
 if(!delta)return opt_enabled(m)?m:0;u32 now=*(volatile u32*)0xfc07000c;
 if(machine_valid&&m==machine_result&&now-machine_stamp<5406720u)return m;
 machine_result=opt_step(m,delta);machine_valid=1;machine_stamp=now;return machine_result;
}
void opt_update(s32 note,char*voice,const char*params){(void)note;(void)voice;(void)params;}
void opt_render(s32*out,char*voice){(void)voice;for(u32 i=0;i<32;i++)out[i]=0;}
u32 opt_noop(void){return 0;}
void opt_draw_marks(u32 canvas,u32 selected){
 u32 n=0;for(u32 i=0;i<25;i++){u32 id=order[i];if(!opt_enabled(id))continue;
  u32 x=68+5*(n%13),y=9+4*(n/13);((void(*)(u32,u32,u32,u32,u32,u32))(id==selected?0x40070efc:0x40070c4e))(canvas,x-4,y,x,y+3,1);n++;
 }
}
/* Sans la machine MIDI, conserver les producteurs MIDI ordinaires. Seuls
 * les anciens sons explicitement en machine17 sont consommes sans emission. */
u32 opt_midi_live(u32 lane,u32 note,u32 velocity){(void)note;(void)velocity;return ((u32(*)(u32,u32))0x4001e318)(0,lane)==17;}
u32 opt_midi_sequence(u32 lane,const u32*event,u32 time,u32 notes){(void)event;(void)time;(void)notes;return lane<6&&((volatile unsigned short*)(0x800015aeu+66*lane))[9]==0x1100;}
