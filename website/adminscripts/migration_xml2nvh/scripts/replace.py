#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import re
import sys


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Substitute string')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    parser.add_argument('from_reg', type=str,
                        help='FROM')
    parser.add_argument('to_reg', type=str,
                        help='TO')
    args = parser.parse_args()

    data = args.input.read()
    args.output.write(re.sub(args.from_reg, args.to_reg, data))

if __name__ == '__main__':
    main()
