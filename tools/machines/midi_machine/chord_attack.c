/* CHORD : raccord de 64 echantillons quand Attack redemarre sur une queue.
 * Le gain Attack natif repart de zero ; sauter directement de la derniere
 * sortie a zero produit un clic. Le raccord suit le filtre, conserve la
 * duree de la rampe native et ne touche pas au chemin Attack=0.
 * Etat propre a chaque piste, utilise uniquement par l'interruption audio.
 */
typedef unsigned int u32;
typedef int s32;
extern volatile u32 mx_attack_gain[6],mx_attack_step[6],mx_attack_machine[6];
volatile u32 mx_attack_delegate;
struct raccord {s32 last,tail,step;u32 remaining,valid;};
static struct raccord tails[6];
static s32 add_sat(s32 a,s32 b){
 u32 x=(u32)a,y=(u32)b,z=x+y;
 if(!((x^y)&0x80000000u)&&((x^z)&0x80000000u))return x&0x80000000u?(s32)0x80000000u:0x7fffffff;
 return (s32)z;
}
static s32 sub_sat(s32 a,s32 b){
 u32 x=(u32)a,y=(u32)b,z=x-y;
 if(((x^y)&0x80000000u)&&((x^z)&0x80000000u))return x&0x80000000u?(s32)0x80000000u:0x7fffffff;
 return (s32)z;
}
void mx_chord_attack(s32 *buffer,u32 lane){
 if(lane>=6)return;
 struct raccord *s=&tails[lane];
 u32 active=mx_attack_machine[lane]==5&&mx_attack_step[lane];
 u32 restart=active&&mx_attack_gain[lane]==0&&s->valid;
 ((void(*)(s32*,u32))mx_attack_delegate)(buffer,lane);
 if(!active){s->valid=0;s->remaining=0;return;}
 if(restart){
  /* Le filtre continu peut encore sonner : compenser le vrai premier
   * echantillon, sans ajouter deux fois sa queue. Difference bornee. */
  s->tail=sub_sat(s->last,buffer[0]);
  s->step=s->tail>>6;s->remaining=64;
 }
 if(s->remaining)for(u32 i=0;i<32;i++){
  buffer[i]=add_sat(buffer[i],s->tail);
  s->tail-=s->step;
  if(!--s->remaining){s->tail=0;break;}
 }
 s->last=buffer[31];s->valid=1;
}
