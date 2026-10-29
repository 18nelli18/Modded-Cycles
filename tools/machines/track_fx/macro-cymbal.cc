// Copyright 2012 Emilie Gillet.
//
// Author: Emilie Gillet (emilie.o.gillet@gmail.com)
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
// 
// See http://creativecommons.org/licenses/MIT/ for more information.
//
// -----------------------------------------------------------------------------
//
// Oscillator - digital style waveforms.

#define private public
#include "braids/digital_oscillator.h"
#undef private

#include <algorithm>
#include <cstdio>

#include "stmlib/utils/dsp.h"
#include "stmlib/utils/random.h"

#include "braids/parameter_interpolation.h"
#include "braids/resources.h"

namespace braids {
  
using namespace stmlib;

static const uint16_t kHighestNote = 140 * 128;
static const uint16_t kPitchTableStart = 128 * 128;
static const uint16_t kOctave = 12 * 128;

static const uint32_t kFIR4Coefficients[4] = { 10530, 14751, 16384, 14751 };
static const uint32_t kFIR4DcOffset = 28208;

uint32_t DigitalOscillator::ComputePhaseIncrement(int16_t midi_pitch) {
  if (midi_pitch >= kPitchTableStart) {
    midi_pitch = kPitchTableStart - 1;
  }
  
  int32_t ref_pitch = midi_pitch;
  ref_pitch -= kPitchTableStart;
  
  size_t num_shifts = 0;
  while (ref_pitch < 0) {
    ref_pitch += kOctave;
    ++num_shifts;
  }
  
  uint32_t a = lut_oscillator_increments[ref_pitch >> 4];
  uint32_t b = lut_oscillator_increments[(ref_pitch >> 4) + 1];
  uint32_t phase_increment = a + \
      (static_cast<int32_t>(b - a) * (ref_pitch & 0xf) >> 4);
  phase_increment >>= num_shifts;
  return phase_increment;
}

static inline void prepare_svf(Svf&s){if(s.dirty_){s.f_=Interpolate824(lut_svf_cutoff,s.frequency_<<17);s.damp_=Interpolate824(lut_svf_damp,s.resonance_<<17);s.dirty_=false;}}
static inline int32_t fixed_svf(Svf&s,int32_t in,bool high){int32_t notch=in-(s.bp_*s.damp_>>15);s.lp_+=s.f_*s.bp_>>15;CLIP(s.lp_);int32_t hp=notch-s.lp_;s.bp_+=s.f_*hp>>15;CLIP(s.bp_);return high?hp:s.bp_;}
void DigitalOscillator::RenderCymbal(
    const uint8_t* sync,
    int16_t* buffer,
    size_t size) { if(!init_ && !svf_[0].punch_ && !svf_[1].punch_ && svf_[0].mode_==SVF_MODE_BP && svf_[1].mode_==SVF_MODE_HP){
  if (init_) {
    svf_[0].Init();
    svf_[0].set_mode(SVF_MODE_BP);
    svf_[0].set_resonance(12000);
    svf_[1].Init();
    svf_[1].set_mode(SVF_MODE_HP);
    svf_[1].set_resonance(2000);
    init_ = false;
  }
  
  HatState* hat = &state_.hat;

  uint32_t increments[7];
  int32_t note = (40 << 7) + (pitch_ >> 1);
  increments[0] = ComputePhaseIncrement(note);
  
  uint32_t root = increments[0] >> 10;
  increments[1] = root * 24273 >> 4;
  increments[2] = root * 12561 >> 4;
  increments[3] = root * 18417 >> 4;
  increments[4] = root * 22452 >> 4;
  increments[5] = root * 31858 >> 4;
  increments[6] = increments[0] * 24;

  int32_t xfade = parameter_[1];
  svf_[0].set_frequency(parameter_[0] >> 1);
  svf_[1].set_frequency(parameter_[0] >> 1);
  
  if(size){prepare_svf(svf_[0]);prepare_svf(svf_[1]);}
  while (size--) {
    phase_ += increments[6];
    if (phase_ < increments[6]) {
      hat->rng_state = hat->rng_state * 1664525L + 1013904223L;
    }
    hat->phase[0] += increments[0];
    hat->phase[1] += increments[1];
    hat->phase[2] += increments[2];
    hat->phase[3] += increments[3];
    hat->phase[4] += increments[4];
    hat->phase[5] += increments[5];
    
    int32_t hat_noise = 0;
    hat_noise += hat->phase[0] >> 31;
    hat_noise += hat->phase[1] >> 31;
    hat_noise += hat->phase[2] >> 31;
    hat_noise += hat->phase[3] >> 31;
    hat_noise += hat->phase[4] >> 31;
    hat_noise += hat->phase[5] >> 31;
    hat_noise -= 3;
    hat_noise *= 5461;
    hat_noise = fixed_svf(svf_[0],hat_noise,false);
    CLIP(hat_noise)
    
    int32_t noise = (hat->rng_state >> 16) - 32768;
    noise = fixed_svf(svf_[1],noise >> 1,true);
    CLIP(noise)
    
    *buffer++ = hat_noise + ((noise - hat_noise) * xfade >> 15);
  }
return;}
  if (init_) {
    svf_[0].Init();
    svf_[0].set_mode(SVF_MODE_BP);
    svf_[0].set_resonance(12000);
    svf_[1].Init();
    svf_[1].set_mode(SVF_MODE_HP);
    svf_[1].set_resonance(2000);
    init_ = false;
  }
  
  HatState* hat = &state_.hat;

  uint32_t increments[7];
  int32_t note = (40 << 7) + (pitch_ >> 1);
  increments[0] = ComputePhaseIncrement(note);
  
  uint32_t root = increments[0] >> 10;
  increments[1] = root * 24273 >> 4;
  increments[2] = root * 12561 >> 4;
  increments[3] = root * 18417 >> 4;
  increments[4] = root * 22452 >> 4;
  increments[5] = root * 31858 >> 4;
  increments[6] = increments[0] * 24;

  int32_t xfade = parameter_[1];
  svf_[0].set_frequency(parameter_[0] >> 1);
  svf_[1].set_frequency(parameter_[0] >> 1);
  
  while (size--) {
    phase_ += increments[6];
    if (phase_ < increments[6]) {
      hat->rng_state = hat->rng_state * 1664525L + 1013904223L;
    }
    hat->phase[0] += increments[0];
    hat->phase[1] += increments[1];
    hat->phase[2] += increments[2];
    hat->phase[3] += increments[3];
    hat->phase[4] += increments[4];
    hat->phase[5] += increments[5];
    
    int32_t hat_noise = 0;
    hat_noise += hat->phase[0] >> 31;
    hat_noise += hat->phase[1] >> 31;
    hat_noise += hat->phase[2] >> 31;
    hat_noise += hat->phase[3] >> 31;
    hat_noise += hat->phase[4] >> 31;
    hat_noise += hat->phase[5] >> 31;
    hat_noise -= 3;
    hat_noise *= 5461;
    hat_noise = svf_[0].Process(hat_noise);
    CLIP(hat_noise)
    
    int32_t noise = (hat->rng_state >> 16) - 32768;
    noise = svf_[1].Process(noise >> 1);
    CLIP(noise)
    
    *buffer++ = hat_noise + ((noise - hat_noise) * xfade >> 15);
  }
}
}
