# SPDX-License-Identifier: MIT
"""Identites stables des parametres et profils de libelles ; aucune E/S appareil."""
from pathlib import Path
import json,re
CATALOG=Path(__file__).with_name('performance_parameters.json')
class RegistryError(ValueError):pass
class Registry:
    def __init__(self,data):
        self.data=data
        if data.get('schema')!=1:raise RegistryError('Unsupported catalog schema')
        self.parameters=data['parameters'];self.by_key={};self.by_route={};identities=set();bindings=set()
        for p in self.parameters:
            scope=p['scope'];key=p['key'];route=p['route_id'];backend=p['backend']
            if scope not in ('track','fx') or backend not in ('sound','level','fx'):raise RegistryError('Unsupported binding backend')
            if (scope=='fx')!=(backend=='fx'):raise RegistryError('Backend scope mismatch')
            if not isinstance(key,int) or not 1<=key<=65535 or not isinstance(route,int) or not 0<=route<=255:raise RegistryError('Invalid identity')
            if key in self.by_key or (scope,route) in self.by_route or p['identity'] in identities:raise RegistryError('Duplicate identity')
            if not re.fullmatch(r'[a-z0-9.]+',p['identity']) or not p['identity'].startswith(scope+'.'):raise RegistryError('Invalid qualified identity')
            if not 0<=p['slot']<33 or not 0<=p['minimum']<=p['maximum']<=0xffff:raise RegistryError('Invalid native range/slot')
            if p['step'] not in (1,256) or p['maximum']%p['step'] or p['minimum']%p['step']:raise RegistryError('Unsupported quantization')
            if not isinstance(p['instance'],int) or not 0<=p['instance']<=255:raise RegistryError('Invalid instance')
            if backend=='level' and (p['slot']!=0 or p['instance']!=0):raise RegistryError('Invalid level binding')
            binding=(backend,p['slot'])
            if binding in bindings:raise RegistryError('Duplicate native binding')
            self.label(p['label']);bindings.add(binding);identities.add(p['identity']);self.by_key[key]=p;self.by_route[scope,route]=p
        self.groups={b:[p for p in self.parameters if p['backend']==b] for b in ('sound','level','fx')}
        if len(self.groups['level'])!=1 or not self.groups['sound'] or not self.groups['fx'] or any(len(v)>31 for v in self.groups.values()):raise RegistryError('Unsupported cache shape')
        self.profiles=data['profiles'];seen=set()
        for profile in self.profiles:
            if profile['name'] in seen:raise RegistryError('Duplicate profile')
            seen.add(profile['name'])
            for scope in ('track','fx'):
                menu=profile[scope+'_menu']
                if not menu or len(set(menu))!=len(menu) or any(k not in self.by_key or self.by_key[k]['scope']!=scope for k in menu):raise RegistryError('Invalid profile menu')
            for k,label in profile['labels'].items():
                if int(k) not in profile['track_menu']+profile['fx_menu']:raise RegistryError('Label for unavailable parameter')
                self.label(label)
        if not self.profiles or self.profiles[0]['name']!='stock':raise RegistryError('Stock fallback required')
    @staticmethod
    def label(value):
        if not isinstance(value,str) or not re.fullmatch(r'[A-Z0-9 :+\-]{1,7}',value):raise RegistryError('Label must fit seven OLED glyphs')
    def resolve(self,scope,route_id):return self.by_route.get((scope,route_id))
    def key(self,scope,route_id):
        p=self.resolve(scope,route_id);return p['key'] if p else None
    def menu(self,profile,scope):return [self.by_key[k]['route_id'] for k in self.profiles[profile][scope+'_menu']]
    def display(self,profile,key):return self.profiles[profile]['labels'].get(str(key),self.by_key[key]['label'])
    def header(self):
        lines=['/* Genere par performance_registry.py ; modifier performance_parameters.json. */',
               'enum { PER_SOUND=0, PER_LEVEL=1, PER_FX=2 };',
               'typedef struct {u16 key;u8 id,slot;u16 minimum,maximum,step;u8 backend,instance;const char *name;} PerParameter;']
        groups={'track':self.groups['sound']+self.groups['level'],'fx':self.groups['fx']}
        for scope,params in groups.items():
            lines.append(f'#define PER_{scope.upper()}_COUNT {len(params)}u')
            lines.append(f'const PerParameter per_{scope}_params[{len(params)}]={{')
            for p in params:
                lines.append(' {%d,%d,%d,%d,%d,%d,%d,%d,%s},'%(p['key'],p['route_id'],p['slot'],p['minimum'],p['maximum'],p['step'],('sound','level','fx').index(p['backend']),p['instance'],json.dumps(p['label'])))
            lines.append('};')
        lines += [f'#define PER_SOUND_COUNT {len(self.groups["sound"])}u',f'#define PER_LEVEL_INDEX {len(self.groups["sound"])}u',f'#define PER_PROFILE_COUNT {len(self.profiles)}u']
        # Les menus conservent les identifiants stables, independamment de leur position.
        for i,profile in enumerate(self.profiles):
            for scope in groups:
                menu=self.menu(i,scope);lines.append(f'const u8 per_menu_{i}_{scope}[]={{'+','.join(map(str,menu))+'};')
                lines.append(f'const char *const per_labels_{i}_{scope}[]={{'+','.join(json.dumps(self.display(i,k)) for k in profile[scope+'_menu'])+'};')
        lines.append('typedef struct {const u8 *track,*fx;const char *const *track_names,*const *fx_names;u32 track_count,fx_count;} PerProfile;')
        lines.append('const PerProfile per_profiles[]={')
        for i,profile in enumerate(self.profiles):lines.append(f' {{per_menu_{i}_track,per_menu_{i}_fx,per_labels_{i}_track,per_labels_{i}_fx,{len(profile["track_menu"])},{len(profile["fx_menu"])}}},')
        lines.append('};')
        return '\n'.join(lines)+'\n'
def load(path=CATALOG):return Registry(json.loads(Path(path).read_text()))
