/* Polarite dans le son : un tag dans le byte bas inutilise de MULT2.
 * Nouveau record88..91 a radix mixte ; ancien format10 reste lisible.
 * Aucun getter UI ni fichier dans le codec ou dans le chemin audio. */
typedef unsigned int u32;typedef unsigned short u16;typedef unsigned char u8;
extern volatile u32 lp_one[6],lp_two[6],lp_dirty,lf2n_epoch;
extern void lp_old_sound_write(u32,u32,u32);
#define N(a) ((u32(*)())(a))
#define TAG 0xa0u
#define FIRST 0x20000000u
#define LIMIT 0x79400000u
static u8 *track_sound(u32 t){u32 p=*(volatile u32*)0x40a78888;return t<6&&p?(u8*)(p+28+t*100):0;}
static u32 tagged(u32 b){return (b&0xfc)==TAG;}
u32 lp_sound_get(u32 t,u32 bank){
 if(t>=6||bank>1)return 0;u8*p=track_sound(t);
 if(p&&p[38]!=17&&tagged(p[79]))return (p[79]>>bank)&1;
 return bank?lp_two[t]:lp_one[t];
}
void lp_sound_set(u32 t,u32 bank,u32 uni){
 if(t>=6||bank>1)return;u8*p=track_sound(t);if(!p||p[38]==17)return;
 u32 flags=tagged(p[79])?p[79]&3:((lp_one[t]&1)|((lp_two[t]&1)<<1));
 flags=(flags&~(1u<<bank))|((uni!=0)<<bank);
 lp_old_sound_write(t,1,((u32)p[78]<<8)|TAG|flags);
}
/* Le potard MULT natif remplace le mot entier : conserver seulement le tag
 * du son courant lorsque le caller n'en fournit pas un nouveau. */
void lp_sound_write(u32 t,u32 field,u32 value){
 if(field==1&&!tagged(value&255)){u8*p=track_sound(t);if(p&&p[38]!=17&&tagged(p[79]))value=(value&0xff00)|p[79];}
 lp_old_sound_write(t,field,value);
}
/* Un son courant ancien sans tag peut migrer lors de son prochain save/copy.
 * Comparaison directe au tableau sons deja publie, sans construire de singleton. */
static u32 source_flags(const u8*p){
 if(tagged(p[79]))return p[79]&3;
 u32 base=*(volatile u32*)0x40a78888,at=(u32)p;
 if(base&&at>=base+28){u32 n=at-base-28;if(n<600&&n%100==0){u32 t=n/100;return (lp_one[t]&1)|((lp_two[t]&1)<<1);}}
 return 4;
}
u32 lp_sound_pack(const u8*p){
 if(p[38]==17)return 0;u32 flags=source_flags(p);if(flags>3)return 0;
 u32 speed=(*(const u16*)(p+76)>>7)&255,mult=p[78],wave=p[80],dest=p[82],depth=(*(const u16*)(p+84)>>7)&255;
 if(mult>23||wave>6||(dest>32&&dest!=127))return 0;if(dest==127)dest=33;
 u32 q=flags;q=q*256+speed;q=q*24+mult;q=q*7+wave;q=q*34+dest;q=q*256+depth;
 return FIRST+q;
}
u32 lp_sound_unpack(u8*p,u32 word){
 if(p[38]==17||word<FIRST||word>=LIMIT)return 0;
 u32 q=word-FIRST,depth=q&255;q>>=8;u32 dest=q%34;q/=34;u32 wave=q%7;q/=7;u32 mult=q%24;q/=24;u32 speed=q&255;q>>=8;
 *(u16*)(p+76)=(u16)(speed<<7);*(u16*)(p+78)=(u16)((mult<<8)|TAG|q);
 *(u16*)(p+80)=(u16)(wave<<8);*(u16*)(p+82)=(u16)((dest==33?127:dest)<<8);*(u16*)(p+84)=(u16)(depth<<7);
 lf2n_epoch++;return 1;
}
