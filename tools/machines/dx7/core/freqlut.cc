/*
 * Copyright 2012 Google Inc.
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

// Resolve frequency signal (1.0 in Q24 format = 1 octave) to phase delta.

// The LUT is just a global, and we'll need the init function to be called before
// use.

#include "synth.h"
#include "freqlut.h"
extern const int32_t dx7_freqlut[1025];
void Freqlut::init(double sample_rate){(void)sample_rate;}
int32_t Freqlut::lookup(int32_t x){
 int i=(x&0xffffff)>>14,lo=x&16383,hi=x>>24;
 uint32_t a=dx7_freqlut[i],d=dx7_freqlut[i+1]-a;
 uint32_t y=a+((d*(uint32_t)lo)>>14);
 if(hi>20)return hi<52?(int32_t)(y<<(hi-20)):0;
 return hi> -12?(int32_t)(y>>(20-hi)):0;
}
