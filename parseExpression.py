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

class docInfo:
    title = ''
    url = ''
    def __init__(self, title, url):
        self.title = title
        self.url = url
    def __str__(self):
        return self.title + " " + self.url

def loadLemmaDict():
    lemmaDict = dict()
    f1 = open("uniq_words_union", 'r')
    f2 = open("norm_stem", 'r')
    for line in f1:
        line2 = f2.readline()
        lemmaDict[line[:-1]] = line2[:-1]
    return lemmaDict

def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

class Stack:
    def __init__(self):
        self.items = []
    def isEmpty(self):
        return self.items == []
    def push(self, item):
        self.items.append(item)
    def pop(self):
        return self.items.pop()
    def peek(self):
        return self.items[len(self.items)-1]
    def size(self):
        return len(self.items)

def skipBytes(f, lenWord):
    read_word = 0
    if lenWord % 4 != 0:
        read_word = 4 - lenWord % 4
    f.read(read_word)

def readPosting(r):
    raw_len_word = r.read(4)
    if raw_len_word == '':
        return (False, "", [])

    len_word = struct.unpack('<I', raw_len_word)[0]

    word = struct.unpack('{}s0'.format(len_word), r.read(len_word))[0]
    skipBytes(r, len_word)

    countEntries = struct.unpack('<I', r.read(4))[0]
    list_entries = list(struct.unpack('<{}I'.format(countEntries), r.read(4 * countEntries)))

    return (True, word, list_entries)

def readForwardDocs(f):
    raw_doc_id = f.read(4)
    if raw_doc_id == '':
        return (False, 0, "", "")
    doc_id = struct.unpack('<I', raw_doc_id)[0]

    len_title = struct.unpack('<I', f.read(4))[0]   
    doc_title = struct.unpack('{}s0'.format(len_title), f.read(len_title))[0]
    skipBytes(f, len_title)

    len_url = struct.unpack('<I', f.read(4))[0]
    doc_url = struct.unpack('{}s0'.format(len_url), f.read(len_url))[0]

    return (True, doc_id, doc_title, doc_url)

def returnSetIntersection(l):
    if l[0] not in ops:
        word = l[0]
        substr = False
        if word[0] == '!':
            substr = True
            word = word[1:]

        word = remove_accents(word.lower()).encode('utf-8')
        if word in lemmaDict:
            word = lemmaDict[word]

        if word in readyRevertIndex:
            return (set(readyRevertIndex[word]), substr)
        else:
            return (set(), substr)
    else:
        start = 1
        cnt_word_need = 1 
        cnt_word_cur = 0

        while cnt_word_cur != cnt_word_need:
            new_start = start + cnt_word_need - cnt_word_cur
            for i in range(start, new_start):
                if l[i] not in ops:
                    cnt_word_cur += 1
                else:
                    cnt_word_need += 1
            start = new_start

        left, sub1 = returnSetIntersection(l[1:start])
        right, sub2 = returnSetIntersection(l[start:])

        if sub1:
            left = allDocIds - left
        if sub2:
            right = allDocIds - right
            
        if l[0] == '&':  
            return (left & right, False)
        elif l[0] == '|':            
            return (left | right, False)

fileRevert = sys.argv[1]
fileForward = sys.argv[2]
r = open(fileRevert, 'rb')
f = open(fileForward, 'rb')
    
readyRevertIndex = dict()
readyForwardIndex = dict()
lemmaDict = loadLemmaDict()

flag = True
while flag:
    flag, word, posting = readPosting(r)
    readyRevertIndex[word] = posting

flag = True
while flag:
    flag, doc_id, doc_title, doc_url = readForwardDocs(f)
    readyForwardIndex[doc_id] = docInfo(doc_title, doc_url)

allDocIds = set(readyForwardIndex.keys())
ops = ["&", "|", ")", "("]

def getReversed(elements):
    st = Stack()
    answer = []

    for el in elements:
        if el not in ops:
            answer.append(el)
        elif el == "(":
            st.push(el)
        elif el == ")":
            while st.peek() != "(":
                answer.append(st.pop())
            st.pop()
        else:
            if st.isEmpty():
                st.push(el)
                continue
            top = st.peek()
            while top != "(":
                answer.append(st.pop())
                if st.isEmpty():
                    break
                else:
                    top = st.peek()
            st.push(el)
            
    while not st.isEmpty():
        answer.append(st.pop())

    answer.reverse()
    return answer

def getQueryResult(expr):
    elements = re.findall(u'!?[a-zа-яА-ЯA-Z0-9,.]+|[&|()]', expr)

    for i in elements:
        print i

    answer = getReversed(elements)
    res, b = returnSetIntersection(answer)
    resDocs = list(res)
    resDocs.sort()

    resDocsForUser = []
    for docId in resDocs:
        resDocsForUser.append(readyForwardIndex[docId])
    return resDocsForUser

res = getQueryResult(u'Вероятность')
for r in res:
    print r

