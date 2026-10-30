/* Arrangement borne ; la lecture utilise la chaine native, jamais une horloge UI. */
#ifndef SONG_H
#define SONG_H
typedef unsigned int song_u32;
typedef unsigned char song_u8;
#define SONG_ROWS 64
#define SONG_CHAIN 64
typedef struct {song_u8 pattern,repeats,mutes,reserved;} song_row;
typedef struct {song_u32 count,loop; song_row rows[SONG_ROWS];} song;
typedef struct {song_u32 pattern,kit;} song_entry;
/* Retourne le nombre d'entrees, ou0 si invalide/trop long. Aucun resultat partiel. */
song_u32 song_compile(const song*,song_entry*,song_u8*,song_u32,song_u32);
song_u32 song_valid(const song*);
#endif
