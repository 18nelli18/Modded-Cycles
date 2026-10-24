/*
 * Copyright 2013 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Low frequency oscillator, compatible with DX7

#include "synth.h"

#include "sin.h"
#include "lfo.h"

// source table
static const uint32_t lfoStep[100]={185017,369883,924162,1293146,1847804,2220802,2769975,3329018,3696759,4250479,4617706,5183239,5547220,6101544,6647939,7024416,7574787,7948236,8502178,8871892,9431204,9969108,10354683,10893244,11277357,11835698,12384179,12752533,13316225,13676991,14243296,14586001,15152288,15724104,16077897,16617980,17011689,17592369,17935813,18484960,19027095,19419278,19967150,20318221,20862714,21449630,21819832,22354033,22742412,23304972,23647745,24204982,24768362,25160172,25693355,26064608,26584589,26987165,27514257,28105006,28423645,28986214,29436149,29930522,33284574,33678653,37164987,40458602,41133661,44647345,48417888,49223510,52865135,56781823,57465674,61631936,62228292,66569148,71011354,71769359,76167173,80389483,81586679,85948081,90802117,92274891,96614401,101521379,102577427,107732447,112999732,114045219,119480330,120551466,126101151,131131781,132779756,138369177,143747959,145730690};


uint32_t Lfo::unit_ = 16794;
uint32_t Lfo::lforatio_ = 2958333;

void Lfo::init(double sample_rate){(void)sample_rate;unit_=16794;lforatio_=2958333;}

void Lfo::reset(const uint8_t params[6]) {
    int rate = params[0];  // 0..99
    delta_ = lfoStep[rate];
    int a = 99 - params[1];  // LFO delay
    if (a == 99) {
        delayinc_ = ~0u;
        delayinc2_ = ~0u;
    } else {
        a = (16 + (a & 15)) << (1 + (a >> 4));
        delayinc_ = unit_ * a;
        a &= 0xff80;
        a = max(0x80, a);
        delayinc2_ = unit_ * a;
    }
    waveform_ = params[5];
    sync_ = params[4] != 0;
}

int32_t Lfo::getsample() {
    phase_ += delta_;
    int32_t x;
    switch (waveform_) {
        case 0:  // triangle
            x = phase_ >> 7;
            x ^= -(phase_ >> 31);
            x &= (1 << 24) - 1;
            return x;
        case 1:  // sawtooth down
            return (~phase_ ^ (1U << 31)) >> 8;
        case 2:  // sawtooth up
            return (phase_ ^ (1U << 31)) >> 8;
        case 3:  // square
            return ((~phase_) >> 7) & (1 << 24);
        case 4:  // sine
            return (1 << 23) + (Sin::lookup(phase_ >> 8) >> 1);
        case 5:  // s&h
            if (phase_ < delta_) {
                randstate_ = (randstate_ * 179 + 17) & 0xff;
            }
            x = randstate_ ^ 0x80;
            return (x + 1) << 16;
    }
    return 1 << 23;
}

int32_t Lfo::getdelay() {
    uint32_t delta = delaystate_ < (1U << 31) ? delayinc_ : delayinc2_;
    uint64_t d = ((uint64_t)delaystate_) + delta;
    if (d > ~0u) {
        return 1 << 24;
    }
    delaystate_ = d;
    if (d < (1U << 31)) {
        return 0;
    } else {
        return (d >> 7) & ((1 << 24) - 1);
    }
}

void Lfo::keydown() {
    if (sync_) {
        phase_ = (1U << 31) - 1;
    }
    delaystate_ = 0;
}
