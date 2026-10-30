/* Relance ACID pour les notes du retrig/arp natif ; DSP existant inchange.
 * Le type partage garantit le contrat de l'etat des bases2.63 epinglees.
 * Les fonctions DSP incluses ici sont eliminees par --gc-sections. */
#define ACID_ENV_SELECT 1
#define ACID_FAST153 1
#define ACID_HOT155 1
#define GOV_SKIP 1
#define acid_update ar_unused_update
#define acid_render ar_unused_render
#include "../fundamentals/acid.c"

extern struct track ar_old_tracks[6];
extern void ar_old_update(s32, char *, const char *);
_Static_assert(sizeof(struct track) == 140, "ACID state layout changed");
_Static_assert(__builtin_offsetof(struct track, held) == 112, "ACID held offset changed");

void ar_update(s32 pmod, char *v, const char *p)
{
 if (*(const u32 *)(v + 0x34)) {
  u32 at = (u32)v;
  if (at >= CYC_VOICE0 && at < CYC_VOICE0 + 6 * CYC_VSTRIDE && (at - CYC_VOICE0) % CYC_VSTRIDE == 0) {
   u32 t = (at - CYC_VOICE0) / CYC_VSTRIDE;
   const volatile s32 *repeat = (const volatile s32 *)(0x40a78d58u + 28 * t);
   /* +4 : duree active (-1 en jeu tenu) ; +20 : evenement natif repete.
    * Un retrig est une nouvelle note, meme si LEN se chevauche ou vaut INF. */
   if (repeat[1] && repeat[5]) ar_old_tracks[t].held = 0;
  }
 }
 ar_old_update(pmod, v, p);
}
