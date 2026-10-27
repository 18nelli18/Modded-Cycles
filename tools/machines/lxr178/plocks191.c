/* Quatre locks independants dans deux slots natifs26/27, valeurs16bits.
 * Le son100octets garde son format A historique. Dans un pas, tag5/mask4/
 * wave3/ratio5 dans26 ; drive7/transient7 dans27. Aucun nouveau fichier.
 * Les bits de presence permettent zero explicite et repli sur le son courant.
 */
typedef unsigned int u32;typedef unsigned short u16;typedef unsigned char u8;typedef int s32;
#define N(a) ((u32(*)())(a))
static u32 ui_cached;
void estus_lock_warm(void){ui_cached=N(0x400cf9a8)();}
static u32 base(u32 t){u32 pool=*(volatile u32*)0x40a78888;if(!pool||t>=6)return 0xa0000040u;const u8*p=(const u8*)(pool+28+100*t);u32 v=((u32)p[72]<<24)|((u32)p[73]<<16)|((u32)p[74]<<8)|p[75];return p[38]==24&&(v>>28)==10?v:0xa0000040u;}
static u32 value(u32 packed,u32 f){return (packed>>(21-7*f))&127;}
static u32 decode(u32 normal,u32 a,u32 b){
 if((a&0xf000)!=0x5000)return normal;
 u32 v[4]={(a>>5)&7,a&31,(b>>7)&127,b&127};
 for(u32 f=0;f<4;f++)if(a&(1u<<(8+f))){u32 max=f==0?4:f==1?16:127;if(v[f]>max)continue;u32 shift=21-7*f;normal=(normal&~(127u<<shift))|(v[f]<<shift);}
 return normal;
}
u32 estus_locked_params(u32 t,u32 packed){return (packed>>28)==5?decode(base(t),packed>>16,packed&65535):packed;}
static u32 read_step(u32 object,u32 t,u32 step,u32 f,u32*word0,u32*word1){
 u32 owner=*(const u32*)(object+44);s32 a=(s32)N(0x4000da2a)(owner,t,step,26),b=(s32)N(0x4000da2a)(owner,t,step,27);
 *word0=a>=0&&(a&0xf000)==0x5000?(u32)a:0x5000;*word1=b>=0?(u32)b:0;
 return value(decode(base(t),*word0,*word1),f);
}
static u32 write_step(u32 object,u32 t,u32 step,u32 f,s32 delta){
 u32 a,b,old=read_step(object,t,step,f,&a,&b),max=f==0?4:f==1?16:127;s32 v=(s32)old+delta;if(v<0)v=0;if(v>(s32)max)v=(s32)max;
 a|=1u<<(8+f);if(f==0)a=(a&~(7u<<5))|((u32)v<<5);else if(f==1)a=(a&~31u)|(u32)v;else if(f==2)b=(b&~(127u<<7))|((u32)v<<7);else b=(b&~127u)|(u32)v;
 if(!N(0x40015c20)(object,step)&&!N(0x40015c7c)(object,step))N(0x40017bb0)(object,step,1);
 N(0x4001646a)(object,step,26,a);N(0x4001646a)(object,step,27,b);return (u32)v;
}
/* Retour1 : lock edite ;0 : geste normal, setter du son historique. */
u32 estus_lock_edit(u32 t,u32 field,s32 delta,u32*out){
 if(t>=6||field>=4)return 0;u32 state=ui_cached=N(0x400cf9a8)();if(!state)return 0;const u8*ui=(const u8*)state;
 u32 grid=ui[357]&&!ui[389],hi=grid?*(const u32*)(state+348):0,lo=grid?*(const u32*)(state+352):0;
 u32 live=!(hi|lo)&&N(0x4006ba76)(state);if(!(hi|lo)&&!live)return 0;
 u32 root=*(volatile u32*)0x40fe4228,pattern=root?N(0x4000f208)(root):0,object=pattern?N(0x4000cfcc)(pattern,t):0;if(!object)return 0;
 u32 limit=N(0x40016402)(object),wrote=0;
 if(live){u32 step=N(0x4006a984)(N(0x400cfd0e)(),t);if(step<64&&step<limit){*out=write_step(object,t,step,field,delta);return 1;}return 0;}
 for(u32 step=0;step<64&&step<limit;step++)if((step<32?lo>>step:hi>>(step-32))&1u){u32 v=write_step(object,t,step,field,delta);if(!wrote)*out=v;wrote=1;}
 return wrote;
}

u32 estus_edit_info(u32 t,u32 machine,u32 engine){
 u32 original=(machine<<8)|engine,state=ui_cached;if(!state||t>=6)return original;const u8*ui=(const u8*)state;
 if(!ui[357]||ui[389])return original;u32 hi=*(const u32*)(state+348),lo=*(const u32*)(state+352);if(!(lo|hi))return original;
 u32 step=0;while(step<64&&!((step<32?lo>>step:hi>>(step-32))&1u))step++;
 u32 root=*(volatile u32*)0x40fe4228,pattern=root?N(0x4000f208)(root):0,object=pattern?N(0x4000cfcc)(pattern,t):0;if(!object||step>=N(0x40016402)(object))return original;
 u32 owner=*(const u32*)(object+44);s32 m=(s32)N(0x4000da2a)(owner,t,step,9),e=(s32)N(0x4000da2a)(owner,t,step,12);if(m>=0)machine=(u32)m>>8;if(e>=0)engine=(u32)e>>8;
 return (machine<<8)|engine;
}
