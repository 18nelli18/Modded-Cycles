/* All Sound Off natif : commande UI, puis reset logique au bloc audio suivant.
 * Aucun E/S, allocation ou effacement des gros rings DDR dans cette commande.
 * Les deux setters natifs gardent leurs arguments et leurs effets originaux.
 * Le chemin ordinaire STOP/pause (valeur0) ne coupe aucune queue. */
typedef unsigned int u32;
extern void mf_old_panic_set(u32),mf_old_panic_transport(u32);
extern void mf_shared_fx_reset(void),lt_panic(void);
extern void pots_reset(void);
extern u32 mf_shared_ch_state[];
volatile u32 mf_fx_panic_pending,mf_fx_panic_count;
void mf_panic_set(u32 value){mf_old_panic_set(value);if(value)mf_fx_panic_pending=1;}
void mf_panic_transport(u32 value){mf_old_panic_transport(value);if(value)mf_fx_panic_pending=1;}
void mf_fx_begin(void){
 if(!mf_fx_panic_pending)return;
 mf_fx_panic_pending=0;
 mf_shared_fx_reset();
 pots_reset();
 /* Meme invalidation des rings chorus que le changement d'effet natif. */
 for(u32 i=2048;i<2062;i++)mf_shared_ch_state[i]=0;
 lt_panic();mf_fx_panic_count++;
}
