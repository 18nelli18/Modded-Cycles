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
// Oscillator - analog style waveforms.

#define private public
#include "braids/analog_oscillator.h"
#undef private

#include "stmlib/utils/dsp.h"

#include "braids/resources.h"
#include "braids/parameter_interpolation.h"

namespace braids { using namespace stmlib;
void AnalogOscillator::RenderTriangleFold(
    const uint8_t* sync_in,
    int16_t* buffer,
    uint8_t* sync_out,
    size_t size) {
 if(parameter_==previous_parameter_) {

  uint32_t phase = phase_;
  
  BEGIN_INTERPOLATE_PHASE_INCREMENT
  int32_t parameter = parameter_;
  
  int16_t gain = 2048 + (parameter * 30720 >> 15);
  while (size--) {

    INTERPOLATE_PHASE_INCREMENT
    
    uint16_t phase_16;
    int16_t triangle;

    
    if (*sync_in++) {
      phase = 0;
    }
    
    // 2x oversampled WF.
    phase += phase_increment >> 1;
    phase_16 = phase >> 16;
    triangle = (phase_16 << 1) ^ (phase_16 & 0x8000 ? 0xffff : 0x0000);
    triangle += 32768;
    triangle = triangle * gain >> 15;
    triangle = Interpolate88(ws_tri_fold, triangle + 32768);
    *buffer = triangle >> 1;
    
    phase += phase_increment >> 1;
    phase_16 = phase >> 16;
    triangle = (phase_16 << 1) ^ (phase_16 & 0x8000 ? 0xffff : 0x0000);
    triangle += 32768;
    triangle = triangle * gain >> 15;
    triangle = Interpolate88(ws_tri_fold, triangle + 32768);
    *buffer++ += triangle >> 1;
  }
  
  END_INTERPOLATE_PARAMETER
  END_INTERPOLATE_PHASE_INCREMENT
    
  phase_ = phase;

 return;
 }

  uint32_t phase = phase_;
  
  BEGIN_INTERPOLATE_PHASE_INCREMENT
  BEGIN_INTERPOLATE_PARAMETER
  
  while (size--) {
    INTERPOLATE_PARAMETER
    INTERPOLATE_PHASE_INCREMENT
    
    uint16_t phase_16;
    int16_t triangle;
    int16_t gain = 2048 + (parameter * 30720 >> 15);
    
    if (*sync_in++) {
      phase = 0;
    }
    
    // 2x oversampled WF.
    phase += phase_increment >> 1;
    phase_16 = phase >> 16;
    triangle = (phase_16 << 1) ^ (phase_16 & 0x8000 ? 0xffff : 0x0000);
    triangle += 32768;
    triangle = triangle * gain >> 15;
    triangle = Interpolate88(ws_tri_fold, triangle + 32768);
    *buffer = triangle >> 1;
    
    phase += phase_increment >> 1;
    phase_16 = phase >> 16;
    triangle = (phase_16 << 1) ^ (phase_16 & 0x8000 ? 0xffff : 0x0000);
    triangle += 32768;
    triangle = triangle * gain >> 15;
    triangle = Interpolate88(ws_tri_fold, triangle + 32768);
    *buffer++ += triangle >> 1;
  }
  
  END_INTERPOLATE_PARAMETER
  END_INTERPOLATE_PHASE_INCREMENT
    
  phase_ = phase;

}
void AnalogOscillator::RenderSineFold(
    const uint8_t* sync_in,
    int16_t* buffer,
    uint8_t* sync_out,
    size_t size) {
 if(parameter_==previous_parameter_) {

  uint32_t phase = phase_;
  
  BEGIN_INTERPOLATE_PHASE_INCREMENT
  int32_t parameter = parameter_;
  
  int16_t gain = 2048 + (parameter * 30720 >> 15);
  while (size--) {

    INTERPOLATE_PHASE_INCREMENT
    
    int16_t sine;

    
    if (*sync_in++) {
      phase = 0;
    }
    
    // 2x oversampled WF.
    phase += phase_increment >> 1;
    sine = Interpolate824(wav_sine, phase);
    sine = sine * gain >> 15;
    sine = Interpolate88(ws_sine_fold, sine + 32768);
    *buffer = sine >> 1;
    
    phase += phase_increment >> 1;
    sine = Interpolate824(wav_sine, phase);
    sine = sine * gain >> 15;
    sine = Interpolate88(ws_sine_fold, sine + 32768);
    *buffer++ += sine >> 1;
  }
  
  END_INTERPOLATE_PARAMETER
  END_INTERPOLATE_PHASE_INCREMENT
  
  phase_ = phase;

 return;
 }

  uint32_t phase = phase_;
  
  BEGIN_INTERPOLATE_PHASE_INCREMENT
  BEGIN_INTERPOLATE_PARAMETER
  
  while (size--) {
    INTERPOLATE_PARAMETER
    INTERPOLATE_PHASE_INCREMENT
    
    int16_t sine;
    int16_t gain = 2048 + (parameter * 30720 >> 15);
    
    if (*sync_in++) {
      phase = 0;
    }
    
    // 2x oversampled WF.
    phase += phase_increment >> 1;
    sine = Interpolate824(wav_sine, phase);
    sine = sine * gain >> 15;
    sine = Interpolate88(ws_sine_fold, sine + 32768);
    *buffer = sine >> 1;
    
    phase += phase_increment >> 1;
    sine = Interpolate824(wav_sine, phase);
    sine = sine * gain >> 15;
    sine = Interpolate88(ws_sine_fold, sine + 32768);
    *buffer++ += sine >> 1;
  }
  
  END_INTERPOLATE_PARAMETER
  END_INTERPOLATE_PHASE_INCREMENT
  
  phase_ = phase;

}
}
