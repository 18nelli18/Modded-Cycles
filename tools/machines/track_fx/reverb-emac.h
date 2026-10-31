/* Produits entiers exacts, avant les memes shifts/divisions historiques.
 * Sauver une fois par bloc les48bits physiques ACC3 et MACSR. */
struct er_context {unsigned int status,acc,ext;};
static __inline__ __attribute__((always_inline)) void er_enter(struct er_context*p){
 __asm__ volatile("move.l %%macsr,%0\n\tmove.l #0,%%macsr\n\tmove.l %%acc3,%1\n\tmove.l %%accext23,%2\n\tmove.l #0,%%acc3":"=&d"(p->status),"=&d"(p->acc),"=&d"(p->ext)::"cc");
}
static __inline__ __attribute__((always_inline)) int er_mul(register int x,register int coefficient){
 register int result;__asm__ volatile("mac.l %1,%2,%%acc3\n\tmovclr.l %%acc3,%0":"=&d"(result):"d"(x),"d"(coefficient):"cc");return result;
}
static __inline__ __attribute__((always_inline)) void er_leave(const struct er_context*p){
 __asm__ volatile("move.l #0,%%macsr\n\tmove.l %0,%%acc3\n\tmove.l %1,%%accext23\n\tmove.l %2,%%macsr"::"d"(p->acc),"d"(p->ext),"d"(p->status):"cc");
}
