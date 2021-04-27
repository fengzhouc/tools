# encoding=utf-8
#
#  Parse command line arguments
#


import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="eg: python dirScan.py -u https://example.com -d top3000 -t path")

    parser.add_argument("-f", help="Load targets from urls, support excel and txt; "
                                   "eg: python dirScan.py -f xx.txt; "
                                   "eg: python dirScan.py -f xx.xls -s 0,1,2")

    parser.add_argument("-s", help="excel sheet number, support more than one, eg: 0,1,2")

    parser.add_argument("-u", help="one url")

    parser.add_argument("-d", help="all/N(topN), default top3000")

    parser.add_argument("-t", help="api/js/html/jsp/do/action/asp/aspx/php/cgi")

    parser.add_argument("-i", help="import data in db, eg: python dirScan.py -t api -i path")

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()
    return args

