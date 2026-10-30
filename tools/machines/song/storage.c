/* Enregistrement projet SGA1 dans le padding v6 +0x40..0x16f.
 * Aucun fichier annexe, aucune E/S audio ; FXP1 +0x1c0 reste intact. */
#include "song.h"
typedef song_u32 u32;typedef song_u8 u8;
extern u32 aa_glide_get(u32),aa_legato_get(u32);
extern void aa_track_set(u32,u32,u32);
extern u32 sg_old_encode(u8*,const u8*,u32,u32,u32),sg_old_decode(u8*,const u8*,u32),sg_old_new(u32);
extern void sg_old_frame(void);
extern void sg_cancel(void);
extern volatile u32 sg_end;
extern volatile u32 sg_page,sg_cursor;
extern volatile u32 sg_active,sg_current;
song sg_song;
static song waiting;
static u8 saved_glide[6],saved_legato[6];
static u32 owner,pending;
#define OFF 0x40
#define SIZE 304
static u32 rd(const u8*p){return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void wr(u8*p,u32 v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static u32 crc(const u8*p,u32 n){u32 c=~0u;while(n--){c^=*p++;for(u32 k=0;k<8;k++)c=c>>1^((0u-(c&1))&0xedb88320u);}return ~c;}
static u32 active(void){u32 p=*(volatile u32*)0x40fe4228;return p?*(volatile u32*)(p+16):0;}
static void defaults(void){waiting.count=0;waiting.loop=0;for(u32 i=0;i<64;i++)waiting.rows[i]=(song_row){0,1,0,0};for(u32 t=0;t<6;t++)saved_glide[t]=saved_legato[t]=1;}
void sg_sync(void){u32 raw=active();if(!raw)return;if(raw==pending){sg_cancel();sg_page=sg_cursor=0;sg_song=waiting;for(u32 t=0;t<6;t++)aa_track_set(t,saved_glide[t],saved_legato[t]);owner=raw;pending=0;}else if(raw!=owner){defaults();pending=raw;sg_sync();}}
u32 sg_encode(u8*out,const u8*raw,u32 limit,u32 flags,u32 cb){
 sg_sync();u32 result=sg_old_encode(out,raw,limit,flags,cb);
 if((result&255)&&out&&(flags&16)&&rd(out)==0xbeefbace&&rd(out+4)==6&&(u32)raw==owner){u8*p=out+OFF;for(u32 i=0;i<SIZE;i++)p[i]=0;wr(p,0x53474131);p[4]=1;p[5]=sg_song.count;p[6]=sg_song.loop;for(u32 i=0;i<64;i++){p[8+4*i]=sg_song.rows[i].pattern;p[9+4*i]=sg_song.rows[i].repeats;p[10+4*i]=sg_song.rows[i].mutes;}for(u32 t=0;t<6;t++){p[264+t]=aa_glide_get(t);p[270+t]=aa_legato_get(t);}wr(p+SIZE-4,crc(p,SIZE-4));}return result;
}
u32 sg_decode(u8*raw,const u8*in,u32 cb){
 u32 result=sg_old_decode(raw,in,cb);if(!(result&255)||!raw||!in)return result;
 defaults();const u8*p=in+OFF;u32 ok=rd(in+4)==6&&rd(p)==0x53474131&&p[4]==1&&p[5]<=64&&p[6]<2&&!p[7]&&rd(p+SIZE-4)==crc(p,SIZE-4);
 if(ok){waiting.count=p[5];waiting.loop=p[6];for(u32 i=0;i<64;i++){waiting.rows[i]=(song_row){p[8+4*i],p[9+4*i],p[10+4*i],p[11+4*i]};}if(waiting.count&&!song_valid(&waiting))ok=0;for(u32 t=0;t<6;t++){if(p[264+t]>127||p[270+t]>1)ok=0;saved_glide[t]=p[264+t];saved_legato[t]=p[270+t];}for(u32 i=276;i<SIZE-4;i++)if(p[i])ok=0;}
 if(!ok)defaults();pending=(u32)raw;sg_sync();return result;
}
u32 sg_new(u32 raw){u32 r=sg_old_new(raw);defaults();pending=raw;sg_sync();return r;}
void sg_frame(void){sg_sync();if(sg_page&&sg_active&&sg_cursor!=sg_current){sg_cursor=sg_current;u32 app=*(volatile u32*)0x40fe4178;if(app)((u32(*)(u32))0x40076bee)(app+64);}if(sg_end&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c)sg_end=0;sg_old_frame();}
