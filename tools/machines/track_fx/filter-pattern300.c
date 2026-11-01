/* Types de filtre par projet/pattern, fichier dedie F3P1.
 * Aucun acces disque depuis le dispatch audio ; six octets seulement par transition.
 * Les anciens reglages globaux ne sont pas importes dans les patterns sans donnee. */
typedef unsigned int u32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 fc_type[6],fp_open,fp_lane,fp_cursor,fp_generation;
extern u32 fp_quiet(void),fp_crc(const u8*,u32);
extern void fp_low(int*,u32),fp_modes(int*,u32);
static u8 bank[96][6];
static u32 owner,generation,project,current,ready,pending,dirty;static volatile u32 revision;
static u32 raw(void){u32 r=*(volatile u32*)0x40fe4228;return r?*(const u32*)(r+16):0;}
static u32 pattern(void){u32 p=*(volatile u32*)0x40a7887c;return p?*(const u32*)(p+30706):96;}
static u32 uuid(u32 r){return r>=0x40000400u&&r<0x42400000u-0x37615cu?*(const u32*)(r+8):0;}
static u32 lock(void){u32 s;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(s)::"memory","cc");return s;}
static void unlock(u32 s){__asm__ volatile("move.w %0,%%sr"::"d"(s):"memory","cc");}
static void capture(void){u32 sr=lock();if(ready&&!pending&&current<96)for(u32 t=0;t<6;t++){u32 v=fc_type[t];if(v>3)v=0;if(bank[current][t]!=v){bank[current][t]=v;dirty=1;revision++;}}unlock(sr);}
static void apply(u32 id){for(u32 t=0;t<6;t++)fc_type[t]=ready&&!pending&&id<96?bank[id][t]:0;fp_open=0;}
void fp_sync(void){u32 sr=lock(),r=raw(),g=fp_generation,id=pattern();if(!ready||r!=owner||g!=generation){if(!pending){pending=1;apply(96);}unlock(sr);return;}if(id!=current){capture();current=id;apply(id);}unlock(sr);}
u32 fp_get(u32 t){fp_sync();return t<6?fc_type[t]:0;}
void fp_set(u32 t,u32 mode){if(t>=6||mode>3)return;fp_sync();fc_type[t]=mode;if(fp_open&&fp_lane==t)fp_open=0;capture();}
static void filename(char*p,u32 id){const char h[]="0123456789abcdef",pre[]="/F3p_";for(u32 i=0;i<5;i++)p[i]=pre[i];for(u32 i=0;i<8;i++)p[5+i]=h[(id>>(28-i*4))&15];p[13]='.';p[14]='c';p[15]='f';p[16]='g';p[17]=0;}
static void load(void){
 u8 packet[592] __attribute__((aligned(4))),extra;u32 h[4]={0};char path[20];u32 r=raw(),id=uuid(r),valid=0;
 if(id){filename(path,id);if(!N(0x4007bc5e)(path,"r",h)){valid=N(0x4007baaa)(packet,592,h)==592&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);const u32*p=(const u32*)packet;if(valid&&(p[0]!=0x46335031||p[1]!=id||p[2]!=576||p[3]!=fp_crc(packet+16,576)))valid=0;if(valid)for(u32 i=0;i<576;i++)if(packet[16+i]>3)valid=0;}}
 u32 sr=lock();owner=r;generation=fp_generation;project=id;for(u32 i=0;i<576;i++)((u8*)bank)[i]=valid?packet[16+i]:0;current=pattern();ready=1;pending=dirty=0;apply(current);unlock(sr);
}
static void save(void){
 u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));if((sr&0x700)||!dirty||!ready||!project)return;
 u8 packet[592] __attribute__((aligned(4)));u32 snapshot=revision;u32*h=(u32*)packet;h[0]=0x46335031;h[1]=project;h[2]=576;for(u32 i=0;i<576;i++)packet[16+i]=((const u8*)bank)[i];if(snapshot!=revision)return;h[3]=fp_crc(packet+16,576);char path[20];filename(path,project);u32 handle[4]={0};
 if(!N(0x4007bc5e)(path,"w",handle)){u32 ok=!N(0x4007bb76)(handle,0,592)&&N(0x4007bb0a)(packet,592,handle)==592&&!N(0x4007e2f6)(handle);if(N(0x4007bc1c)(handle))ok=0;if(ok&&snapshot==revision)dirty=0;}
}
static void center(u32 t){u32 root=N(0x400cf866)();if(!root)return;u32 kit=N(0x4000eb9c)(root);if(!kit)return;u32 obj=N(0x40009c1a)(kit,t);if(!obj)return;u32 rec[2]={24,0x40000000u},pair[2]={(u32)rec,(u32)(rec+2)};N(0x4001416c)(obj,pair);}
void fp_frame(void){
 fp_sync();u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));if(sr&0x700)return;
 /* Le disque reste reserve au service UI a l arret. */
 if(!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c&&fp_quiet()){
  if(pending&&raw()){if(dirty)save();if(!dirty)load();}
  else if(ready&&owner==raw()&&generation==fp_generation){u32 id=uuid(owner);if(!project&&id){project=id;dirty=1;}}
 }
 if(fp_open&&(!N(0x4007faf4)(13)||!N(0x4007faf4)(5))){static const u8 order[4]={1,0,2,3};if(fp_lane<6&&fp_cursor<4){u32 mode=order[fp_cursor];if(mode==3&&fc_type[fp_lane]!=3)center(fp_lane);fc_type[fp_lane]=mode;}fp_open=0;capture();u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
 capture();if(!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c&&fp_quiet())save();
}
/* Seulement les transitions : aucun nouveau dispatch par piste/bloc. */
extern void fp_old_change(u32),fp_old_lfosync(u32,u32);
void fp_change(u32 ptr){capture();fp_old_change(ptr);fp_sync();}
void fp_lfosync(u32 ctx,u32 frame){fp_sync();fp_old_lfosync(ctx,frame);}

/* Presse-papiers natifs : memes pointeurs et meme duree de vie que MFX. */
extern u32 fp_old_copy(u32,u32,u32),fp_old_init(u8*,u32),fp_old_encode(u8*,const u8*,u32,u32,u32);
static struct {u32 ptr;u8 modes[6];} clips[8];static u32 clip_cursor;
static u32 index_of(u32 ptr){if(!owner||ptr<owner+28)return 96;u32 d=ptr-owner-28;return d<96*30710u&&d%30710u==0?d/30710u:96;}
static void get_row(u32 ptr,u8*out){capture();u32 id=index_of(ptr);if(ready&&id<96){for(u32 t=0;t<6;t++)out[t]=bank[id][t];return;}for(u32 i=0;i<8;i++)if(clips[i].ptr==ptr){for(u32 t=0;t<6;t++)out[t]=clips[i].modes[t];return;}for(u32 t=0;t<6;t++)out[t]=0;}
static void put_row(u32 ptr,const u8*in){u32 id=index_of(ptr);if(ready&&id<96){u32 sr=lock();for(u32 t=0;t<6;t++)bank[id][t]=in[t];if(current==id)apply(id);dirty=1;revision++;unlock(sr);return;}u32 n=8;for(u32 i=0;i<8;i++)if(clips[i].ptr==ptr){n=i;break;}if(n==8)n=clip_cursor++&7;clips[n].ptr=ptr;for(u32 t=0;t<6;t++)clips[n].modes[t]=in[t];}
u32 fp_copy(u32 dst,u32 src,u32 bytes){u8 row[6];if(bytes==30710)get_row(src,row);u32 r=fp_old_copy(dst,src,bytes);if(bytes==30710)put_row(dst,row);return r;}
u32 fp_init(u8*ptr,u32 flags){u32 r=fp_old_init(ptr,flags);u8 row[6]={0,0,0,0,0,0};if(ptr&&ready)put_row((u32)ptr,row);return r;}
u32 fp_encode(u8*out,const u8*in,u32 limit,u32 flags,u32 cb){fp_sync();capture();u32 r=fp_old_encode(out,in,limit,flags,cb);if((r&255)&&(flags&16)&&(u32)in==owner)save();return r;}
