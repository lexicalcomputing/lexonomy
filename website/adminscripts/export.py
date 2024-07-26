#!/usr/bin/python3.10
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ops


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import NVH/XML to dictionary with init and config')
    parser.add_argument('dict_id', type=str,
                        help='import file name')
    parser.add_argument('-f', '--format', type=str,
                        required=False, default='nvh',
                        help='Format of the output. Available nvh, xml.')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    args = parser.parse_args()

    dictDB = ops.getDB(args.dict_id)
    for line in ops.download(dictDB, args.dict_id, args.format):
        args.output.write(line)

    dictDB.close()


if __name__ == '__main__':
    main()