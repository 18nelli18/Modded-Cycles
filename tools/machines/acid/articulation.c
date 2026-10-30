/* Prototype : duree de convergence a90%, independante du tempo.
 * Reglages 1..127 : 50..360ms ; 0 coupe le glide sans retrigger du filtre. */
typedef unsigned int u32;typedef int s32;
volatile u32 aa_legato[6],aa_glide[6],aa_initialized[6];
u32 aa_legato_get(u32 t){return t<6?(aa_initialized[t]?aa_legato[t]:1):0;}
u32 aa_glide_get(u32 t){return t<6?(aa_initialized[t]?aa_glide[t]:1):0;}
void aa_track_set(u32 t,u32 glide,u32 legato){if(t<6&&glide<128&&legato<2){aa_glide[t]=glide;aa_legato[t]=legato;aa_initialized[t]=1;}}
s32 aa_glide_coefficient(u32 setting){
 if(!setting)return 0x7fffffff;
 if(setting>127)setting=127;
 /* Interpolation des coefficients RC, table calculee hors interruption. */
 extern const s32 aa_coefficients[128];return aa_coefficients[setting];
}
