# encoding=utf-8
#
#  Parse command line arguments
#


import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(usage='python TitleScan.py -f [domain/ip filename]')

    parser.add_argument("-f", help="Load new line delimited targets from domainFile")

    parser.add_argument("-p", help="multiprocessing pool size, default:os.cpu_count()")

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()
    return args

