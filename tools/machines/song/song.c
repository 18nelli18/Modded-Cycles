#include "song.h"
song_u32 song_valid(const song*s){
 if(!s||!s->count||s->count>SONG_ROWS||s->loop>1)return 0;
 song_u32 total=0;
 for(song_u32 i=0;i<s->count;i++){
  const song_row*r=&s->rows[i];
  if(r->pattern>=96||!r->repeats||r->repeats>64||r->mutes>63||r->reserved)return 0;
  total+=r->repeats;
 }return total;
}
song_u32 song_compile(const song*s,song_entry*out,song_u8*row_map,song_u32 patterns,song_u32 kits){
 song_u32 total=song_valid(s);if(!total||total>SONG_CHAIN||!out||!row_map)return 0;
 song_u32 pos=0;
 for(song_u32 i=0;i<s->count;i++)for(song_u32 n=0;n<s->rows[i].repeats;n++){
  out[pos].pattern=patterns+0x77f6u*s->rows[i].pattern;
  out[pos].kit=kits+0x1bb6u*s->rows[i].pattern;
  row_map[pos++]=(song_u8)i;
 }return total;
}
