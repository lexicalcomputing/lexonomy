#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ops


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Delete dict from lexonomy')
    parser.add_argument('dictID', type=str,
                        help='Dict ID')
    args = parser.parse_args()
    ops.destroyDict(args.dictID)


if __name__ == '__main__':
    main()