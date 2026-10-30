/* La chaine native choisit le prochain pattern ; cette couche suit son index. */
#include "song.h"
typedef song_u32 u32;
#define N(a) ((u32(*)())(a))
extern song sg_song;
extern void sg_sync(void);
extern u32 sg_chain_original(const song_entry*,u32);
static song_entry entries[64];static song_u8 row_map[64];
volatile u32 sg_active,sg_current,sg_end;
static u32 count,seen,last,project;
u32 sg_start(void){
 if(*(volatile u32*)0x40a78874||*(volatile u32*)0x40a7883c)return 0;
 sg_sync();u32 obj=*(volatile u32*)0x40fe4228,raw=obj?*(volatile u32*)(obj+16):0;if(!raw)return 0;
 count=song_compile(&sg_song,entries,row_map,raw+28,raw+28+96*0x77f6u);if(!count)return 0;
 project=raw;seen=sg_end=sg_current=sg_active=0;last=0;
 N(0x40055cd6)(entries,count);seen=sg_active=1;return 1;
}
void sg_cancel(void){sg_active=sg_end=seen=0;}
u32 sg_chain_set(const song_entry*chain,u32 n){sg_cancel();return sg_chain_original(chain,n);}
void sg_boundary(u32 pattern){
 if(!sg_active)return;
 u32 obj=*(volatile u32*)0x40fe4228,raw=obj?*(volatile u32*)(obj+16):0;
 u32 previous=*(volatile u32*)0x40a78634;
 if(raw!=project||previous>=count){sg_cancel();return;}
 /* Dans l'ISR, l'index a deja ete avance avant la publication du pattern. */
 u32 index=previous;
 if(pattern!=entries[index].pattern){sg_cancel();return;}
 if(seen&&index==0&&last==count-1&&!sg_song.loop){sg_end=1;sg_active=0;N(0x40055f14)();return;}
 sg_current=row_map[index];last=index;seen=1;
}
u32 sg_mutes(void){if(sg_end)return 63;return sg_active&&sg_current<sg_song.count?sg_song.rows[sg_current].mutes:0;}
