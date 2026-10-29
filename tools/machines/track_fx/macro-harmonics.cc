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

#include "braids/digital_oscillator.h"
 #include "stmlib/utils/dsp.h"
 #include "braids/resources.h"
 namespace braids { using namespace stmlib;
 struct TargetCache {const void*owner;uint32_t valid,inc;int32_t a,b;int32_t target[12];};
 static TargetCache target_cache[6];
 static TargetCache* cache_for(const void*owner) {
  for(unsigned i=0;i<6;i++)if(target_cache[i].owner==owner)return &target_cache[i];
  for(unsigned i=0;i<6;i++)if(!target_cache[i].owner){target_cache[i].owner=owner;return &target_cache[i];}
  target_cache[0].owner=owner;target_cache[0].valid=0;return &target_cache[0];
 }
 void DigitalOscillator::RenderHarmonics(
    const uint8_t* sync,
    int16_t* buffer,
    size_t size) {
  uint32_t phase = phase_;
  int16_t previous_sample = state_.add.previous_sample;
  uint32_t phase_increment = phase_increment_ << 1;
  TargetCache* cache=cache_for(this);
  int32_t* target_amplitude=cache->target;
  int32_t amplitude[kNumAdditiveHarmonics];
  
  if(!cache->valid || cache->inc!=phase_increment_ || cache->a!=parameter_[0] || cache->b!=parameter_[1]) {
   int32_t peak = (kNumAdditiveHarmonics * parameter_[0]) >> 7;
  int32_t second_peak = (peak >> 1) + kNumAdditiveHarmonics * 128;
  int32_t second_peak_amount = parameter_[1] * parameter_[1] >> 15;

  int32_t sqrtsqrt_width = parameter_[1] < 16384
      ? parameter_[1] >> 6 : 511 - (parameter_[1] >> 6);
  int32_t sqrt_width = sqrtsqrt_width * sqrtsqrt_width >> 10;
  int32_t width = sqrt_width * sqrt_width + 4;
  int32_t total = 0;
  for (size_t i = 0; i < kNumAdditiveHarmonics; ++i) {
    int32_t x = i << 8;
    int32_t d, g;

    d = (x - peak);
    g = 32768 * 128 / (128 + d * d / width);
    
    d = (x - second_peak);
    g += second_peak_amount * 128 / (128 + d * d / width);
    total += g;
    target_amplitude[i] = g;
  }
  
  int32_t attenuation = 2147483647 / total;
  for (size_t i = 0; i < kNumAdditiveHarmonics; ++i) {
    if ((phase_increment >> 16) * (i + 1) > 0x4000) {
      target_amplitude[i] = 0;
    } else {
      target_amplitude[i] = target_amplitude[i] * attenuation >> 16;
    }

  }
  
    cache->inc=phase_increment_;cache->a=parameter_[0];cache->b=parameter_[1];cache->valid=1;
   }
   for(size_t i=0;i<kNumAdditiveHarmonics;i++)amplitude[i]=state_.hrm.amplitude[i];
   size_t active_harmonics=kNumAdditiveHarmonics;
  while(active_harmonics && target_amplitude[active_harmonics-1]==0 && amplitude[active_harmonics-1]==0)--active_harmonics;
  while (size) {
    int32_t out;
    
    phase += phase_increment;
    if (*sync++ || *sync++) {
      phase = 0;
    }
    out = 0;
    for (size_t i = 0; i < active_harmonics; ++i) {
      out += Interpolate824(wav_sine, phase * (i + 1)) * amplitude[i] >> 15;
      amplitude[i] += (target_amplitude[i] - amplitude[i]) >> 8;
    }
    CLIP(out)
    *buffer++ = (out + previous_sample) >> 1;
    *buffer++ = out;
    previous_sample = out;
    size -= 2;
  }
  state_.add.previous_sample = previous_sample;
  phase_ = phase;
  for (size_t i = 0; i < kNumAdditiveHarmonics; ++i) {
    state_.hrm.amplitude[i] = amplitude[i];
  }
}

}
