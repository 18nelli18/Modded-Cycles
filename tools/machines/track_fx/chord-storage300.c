/* ChordKeys Optional : six configurations de26bits dans header40..59.
 * Le champ Page Length60..63 et les six octets Page TRK restent independants.
 * Extensions base5/17bits, racine5bits, mode3bits et ON1bit ; cache a la lecture.
 * Seules les editions conservant ChordKeys installent ces fonctions. */
typedef unsigned int u32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#define DEFAULT (48u<<21)
#define MAGIC 0x434b0400u
extern u32 cs_valid(u32),cs_irq_save(void);extern void cs_irq_restore(u32),cs_clear_header(const void*),cs_clear_modifiers(u32,const void*);
extern u8*cs_object(void);extern u8*cs_audio_header(void);extern u8*cs_ui_header(void);
static u32 keys[6],values[6],valid_mask;
static u32 get(const u8*p){return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3];}
static void put(u8*p,u32 v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static u32 signature(u32 m){return m==0x434b01a7u||(m&~63u)==0x434b0200u||(m&~63u)==0x434b0300u||(m&~63u)==MAGIC;}
static u32 midi(const u8*h){if(!h)return 0;u32 m=get(h+32);return ((m&~63u)==0x434b0300u||(m&~63u)==MAGIC)?m&63:0;}
static u32 encode(u32 w){u32 x=0,p=1;for(u32 i=0;i<7;i++){x+=((w>>(3*i))&7)*p;p*=5;}return x|((((w>>21)&127)-24)<<17)|(((w>>28)&7)<<22)|((w>>31)<<25);}
static u32 field(const u8*h,u32 t){u32 bit=4+26*t;return (get(h+40+(bit>>3))>>(6-(bit&7)))&0x3ffffff;}
static u32 decode(u32 x){u32 root=(x>>17)&31,mode=(x>>22)&7,ext=x&0x1ffff;if(root>24||mode>6||ext>=78125)return DEFAULT;u32 w=((x>>25)<<31)|(mode<<28)|((root+24)<<21);for(u32 i=0;i<7;i++){w|=(ext%5)<<(3*i);ext/=5;}return w;}
u32 cs_read(const u8*h,u32 t){
 if(!h||t>=6)return DEFAULT;u32 m=get(h+32);if(!signature(m))return DEFAULT;
 if((m&~63u)!=MAGIC){u32 w=get(h+40+4*t);return cs_valid(w)?w:DEFAULT;}
 if((h[40]&240)!=160)return DEFAULT;u32 x=field(h,t);if((valid_mask&(1u<<t))&&keys[t]==x)return values[t];
 u32 w=decode(x),sr=cs_irq_save();values[t]=w;keys[t]=x;valid_mask|=1u<<t;cs_irq_restore(sr);return w;
}
static void write_field(u8*h,u32 t,u32 w){u32 bit=4+26*t,shift=6-(bit&7);u8*p=h+40+(bit>>3);u32 x=get(p),mask=0x3ffffffu<<shift;put(p,(x&~mask)|(encode(w)<<shift));}
static void store(u8*h,const u32*w,u32 flags){for(u32 i=0;i<20;i++)h[40+i]=0;h[40]=160;for(u32 t=0;t<6;t++)write_field(h,t,w[t]);put(h+32,MAGIC|(flags&63));}
void cs_reset(u8*h){if(!h)return;u32 w[6];for(u32 i=0;i<6;i++)w[i]=DEFAULT;u32 sr=cs_irq_save();cs_clear_header(h);store(h,w,0);cs_irq_restore(sr);}
void cs_load(u8*d,const u8*s){if(!d||!s)return;u32 w[6];for(u32 t=0;t<6;t++)w[t]=cs_read(s,t);u32 flags=midi(s),sr=cs_irq_save();cs_clear_header(d);store(d,w,flags);cs_irq_restore(sr);}
static void migrate(u8*h){if((get(h+32)&~63u)!=MAGIC||(h[40]&240)!=160){u32 w[6];for(u32 t=0;t<6;t++)w[t]=cs_read(h,t);u32 flags=midi(h);store(h,w,flags);}}
void cs_set(u32 t,u32 w){if(t>=6||!cs_valid(w))return;u8*object=cs_object();u8*h=object?*(u8**)(object+16):0;if(!h)return;u32 sr=cs_irq_save();cs_clear_modifiers(t,h);migrate(h);write_field(h,t,w);cs_irq_restore(sr);N(*(u32*)(*(u32*)object+16))(object,0);}
u32 cs_ui_midi_get(u32 t){return t<6?(midi(cs_ui_header())>>t)&1:0;}
u32 cs_audio_midi_get(u32 t){return t<6?(midi(cs_audio_header())>>t)&1:0;}
void cs_ui_midi_set(u32 t,u32 on){if(t>=6||on>1)return;u8*object=cs_object();u8*h=object?*(u8**)(object+16):0;if(!h)return;u32 sr=cs_irq_save();migrate(h);put(h+32,(get(h+32)&~(1u<<t))|(on<<t));cs_irq_restore(sr);N(*(u32*)(*(u32*)object+16))(object,0);}
