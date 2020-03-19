# encoding=utf-8
#
#  Parse command line arguments
#


import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="dicts mast set in lib/config.py")

    parser.add_argument("-f", help="Load new line delimited targets(excel) from urls")

    parser.add_argument("-s", help="excel sheet number, support more than one, eg: 0,1,2")

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()
    return args

