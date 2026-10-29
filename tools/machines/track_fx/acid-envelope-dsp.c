/* Meme noyau ACID ; branche F conserve toutes les operations historiques. */
#define ACID_ENV_SELECT 1
#define ACID_FAST153 1
#define ACID_HOT155 1
#define GOV_SKIP 1
#define acid_update ae_update
#define acid_render ae_render
#include "../fundamentals/acid.c"
