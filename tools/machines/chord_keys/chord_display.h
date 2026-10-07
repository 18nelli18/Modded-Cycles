#ifndef CHORD_DISPLAY_H
#define CHORD_DISPLAY_H

/* Instantané atomique du dernier accord calculé par piste. Le thread UI ne
 * recalcule ni COLOR ni les gestes : il lit les intervalles réellement résolus.
 * Bits 0..6 : note MIDI ; 7..9 : premier intervalle (0 ou 7) ; bit 10 : limite
 * aiguë native ; 12/17/22 : les trois autres intervalles non disposés (5 bits) ;
 * 27..30 : basse disposée modulo 12 ; 31 : valide. Une quatrième case nulle
 * identifie la triade. Les notes décrivent l'accord harmonique demandé ; HIGH
 * LIMIT signale une voix coupée ou plafonnée par la protection aiguë de l'OS.
 * PITCH/FINE restent des transpositions natives du timbre.
 */
#define CK_CHORD_LIMITED 0x400u
extern volatile unsigned int ck_chord_live[6];
unsigned int ck_chord_packet(unsigned int note, const unsigned int intervals[4],
                             unsigned int count, unsigned int voiced_bass);
void ck_chord_live_publish(unsigned int track, unsigned int note,
                           const unsigned int intervals[4], unsigned int count,
                           unsigned int voiced_bass);

/* Deux sorties de 24 octets : symbole musical puis omissions explicites.
 * Les deux chaînes sont vides si l'instantané n'est pas valide. Les altérations
 * et inversions viennent des intervalles ; aucune table de noms par degré.
 */
void ck_chord_name(unsigned int packet, char name[24], char omissions[24]);

#endif
