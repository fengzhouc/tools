# encoding=utf-8
#
#  Parse command line arguments
#


import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="dicts mast set in lib/config.py")

    parser.add_argument("-f", help="Load targets from urls, support excel and txt; "
                                   "eg: python dnsquery.py -f xx.txt -t A"
                                   "eg: python dnsquery.py -f xx.xls -s 0,1,2 -c 1 -t A")

    parser.add_argument("-s", help="excel sheet number, support more than one, eg: 0,1,2")

    parser.add_argument("-c", help="excel col number")

    parser.add_argument("-t", help="dns query type, A,AAA,TXT,MX,SOA,PTR")

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()
    return args

