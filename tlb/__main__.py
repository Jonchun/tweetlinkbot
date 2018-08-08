#!/usr/bin/env python3
# coding: utf-8

import os.path
import sys

# https://stackoverflow.com/questions/38417694/purpose-of-some-boilerplate-code-in-main-py
if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of __main__.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

def main(argv=None):
    try:
        from tlb.core import main
        sys.exit(main())
    except Exception as e:
        sys.exit(e)

if __name__ == '__main__':
    main()