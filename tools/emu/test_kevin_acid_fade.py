#!/usr/bin/env python3
"""Cœur ACID Kevin dans la boucle audio native : retrigs et slides.

Référence C du même DSP, machines stock inchangées, démarrage PACK réel.
"""
import argparse,json,pathlib,tempfile
import test_acid as t
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--recipe',required=True);a=p.parse_args()
 stock=t.T.main_os_from_syx(a.cycles);fw=t.Fw(stock,[json.loads(pathlib.Path(a.recipe).read_text())]);off=t.Fw(stock,[])
 with tempfile.TemporaryDirectory() as d:
  ref=t.Ref(pathlib.Path(d));t.exact(fw,ref,t.cases(True)[:2]+t.cases(True)[-5:],'ACID Kevin');t.stock_unchanged(off,fw,'stock inchangé');t.boot(fw)
 assert not t.t7.FAIL,t.t7.FAIL
 print('PASS : fondu compilé, retrigs, slides, machines stock et boot')
if __name__=='__main__':main()
