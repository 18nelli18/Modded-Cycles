/* Reveil FX natifs : les voix seches seules ne reveillent plus delay/reverbe.
 * Les retours restent calcules pendant16384blocs silencieux avant veille.
 * Le mecanisme Model-TG conserve DMA, queues et sorties au reveil. */
typedef unsigned int u32;typedef int s32;
extern volatile u32 ch_mode,cr_mode,idle_rev_active,idle_del_active;
static u32 idle_started,idle_woken;
u32 idle_present(void){
 u32 sent=0,present=idle_woken&&(ch_mode||cr_mode||idle_rev_active||idle_del_active);
 static const u32 gain[4]={0x40a78bd0,0x40a78bb8,0x40a78b9c,0x40a78b80};
 for(u32 k=0;k<4&&!sent&&!present;k++){
  volatile u32*p=(volatile u32*)gain[k];
  sent=!!(p[0]|p[1]|p[2]|p[3]|p[4]|p[5]);
 }
 if(sent)idle_woken=1;
 /* Une selection memorisee ne cree pas de queue avant le premier send.
  * Apres le premier signal, conserver les transitions et queues du222. */
 present|=sent;
 /* BSS neuf seulement : aucune queue ne peut encore exister. Le demarrage
  * sec ne paie pas16384blocs de DSP avant la premiere mise en veille. */
 if(!idle_started){idle_started=1;if(!present){
  *(volatile u32*)0x401b72ec=1;*(volatile u32*)0x401b72f0=1;
  *(volatile u32*)0x401b72fc=16384;
 }}
 if(present){*(volatile u32*)0x401b72ec=0;*(volatile u32*)0x401b72f0=0;*(volatile u32*)0x401b72fc=0;}
 return present;
}
