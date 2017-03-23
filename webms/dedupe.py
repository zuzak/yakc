#!/usr/bin/env python3
import os
import hashlib
from time import strftime

hashes = dict()
FN = 'all'


def compute_hash(fname):
    # http://stackoverflow.com/a/3431838
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def purge_file(fn, md5=''):
    string = strftime('%Y-%m-%d %H:%M:%S sysadmin purged duplicate ' + md5)
    with open(os.path.join('metadata', fn), 'a') as lf:
        lf.write(string + '\n')
    dirs = ['bad', 'held', 'music', 'veto', 'trash', 'best', 'decent', 'all']
    for directory in dirs:
        try:
            os.remove(os.path.join(directory, fn))
        except OSError:
            pass


files = os.listdir(FN)
count1 = 0
count2 = 0
for filename in files:
    size = os.path.getsize(os.path.join(FN, filename))
    if size in hashes:
        h = compute_hash(os.path.join(FN, filename))
        if h in hashes[size]:
            count1 = count1 + 1
            purge_file(filename, h)
        else:
            hashes[size].append(h)
            count2 = count2 + 1
    else:
        hashes[size] = [compute_hash(os.path.join(FN, filename))]
        count2 = count2 + 1
    print('\rDeleted {0}/{1} files'.format(count1, count2), end='')
print()
