# -*- encoding: utf-8 -*-

import unidecode
import unicodedata
import sys
import json
import string
import re
import time
import os
import struct

fileRevert = sys.argv[1]

r = open(fileRevert, 'rb')

def skipBytes(f, lenWord):
    read_word = 0
    if lenWord % 4 != 0:
        read_word = 4 - lenWord % 4
    return read_word

def readPosting(r):
    raw_len_word = r.read(4)
    if raw_len_word == '':
        return (False, "", dict())

    len_word = struct.unpack('<I', raw_len_word)[0]

    word = struct.unpack('{}s0I'.format(len_word), r.read(len_word + skipBytes(len_word)))[0]

    countEntries = struct.unpack('<I', r.read(4))[0]

    entries = dict()

    for i in xrange(countEntries):
        docId = struct.unpack('<I', r.read(4))[0]
        coordsLen = struct.unpack('<I', r.read(4))[0]
        coords = list(struct.unpack('<{}I'.format(coordsLen), r.read(4 * coordsLen)))
        entries[docId] = coords

    return (True, word, entries)
    
readyRevertIndex = dict()

flag = True
while flag:
    flag, word, posting = readPosting(r)
    if flag == False:
        break
    readyRevertIndex[word] = posting

post = len(readyRevertIndex["москва"].keys())
print post


