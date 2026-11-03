"""Diffusion native economique : quatre etages, cadence et memoires conservees."""
BASE=0x40000400
AT=0x40057b4a
def apply(native):
    old=bytes.fromhex('7608');new=bytes.fromhex('7604')
    assert native[AT-BASE:AT-BASE+2]==old
    native[AT-BASE:AT-BASE+2]=new
    return dict(patches=[dict(at=AT,old=old.hex(),new=new.hex())],allpass_stages=4,previous_allpass_stages=8,sample_rate=48000,delay_lengths_unchanged=True,new_state_bytes=0,quality_changed=True,hardware_tested=False)
