"""
Pyntacle tests manager script.
"""
import sys
import os
import hashlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))


def getmd5(filein):
    with open(filein,'r') as file:
        f = file.read().rstrip('\r')
    return hashlib.md5(bytes(f, 'utf-8')).hexdigest()


def getmd5_bin(filein):
    with open(filein,'rb') as file:
        f = file.read()
    return hashlib.md5(f).hexdigest()
