typedef unsigned int u32;typedef int s32;
extern volatile u32 rm_machine_valid,rm_machine_stamp,rm_machine_result;
extern u32 mf_old_machine_get(u32,u32),mf_old_machine_set(u32,u32,u32,u32);
/* Builder supplies rm_order and rm_count for the actual edition. */
extern const unsigned char rm_order[];extern const u32 rm_count;
u32 rm_noop(void){return 0;}
void rm_silence(s32*out,void*v){(void)v;for(u32 i=0;i<32;i++)out[i]=0;}
u32 rm_step(u32 machine,s32 delta){
 if(machine==21)machine=4;u32 pos=0;for(u32 i=0;i<rm_count;i++)if(rm_order[i]==machine)pos=i;
 if(!delta)return rm_order[pos];u32 now=*(volatile u32*)0xfc07000c;
 if(rm_machine_valid&&machine==rm_machine_result&&now-rm_machine_stamp<5406720u)return machine;
 if(delta>0&&pos+1<rm_count)pos++;if(delta<0&&pos)pos--;
 rm_machine_valid=1;rm_machine_stamp=now;return rm_machine_result=rm_order[pos];
}
u32 rm_machine_get(u32 object,u32 lane){u32 m=mf_old_machine_get(object,lane);return m==21?4:m;}
u32 rm_machine_set(u32 object,u32 machine,u32 flags,u32 mode){return mf_old_machine_set(object,machine==21?4:machine,flags,mode);}
