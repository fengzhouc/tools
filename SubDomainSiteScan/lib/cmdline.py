# encoding=utf-8
#
#  Parse command line arguments
#


import argparse
import sys
import os


def parse_args():
    parser = argparse.ArgumentParser(usage='SubDomainSiteScan.py -f [domain filename]')

    # parser.add_argument("-h", help="help")

    parser.add_argument("-f", help="Load new line delimited targets from TargetFile")

    parser.add_argument("-p", help="multiprocessing pool size, default:16")

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()
    return args

