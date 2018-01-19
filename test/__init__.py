"""
Dedalus' tests manager script.

"""
import sys
import os
import hashlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))


def getmd5(filein):
    return hashlib.md5(bytes(open(filein, 'r').read().rstrip('\r'), 'utf-8')).hexdigest()


def getmd5_bin(filein):
    return hashlib.md5(open(filein, 'rb').read()).hexdigest()