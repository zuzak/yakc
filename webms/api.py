#!/usr/bin/env python3
from requests import get
from time import strftime
import os
import sys

PROTOCOL = 'http'
BOARD = 'wsg'

API_URL = PROTOCOL + '://a.4cdn.org/' + BOARD + '/'
CDN_URL = PROTOCOL + '://i.4cdn.org/' + BOARD + '/'
FILE_DIR = 'all'

CATALOG_URL = API_URL + '/threads.json'

catalog_req = get(CATALOG_URL)
if catalog_req.status_code != 200:
    raise Exception('Cannot get threads')

pages = catalog_req.json()

sys.stdout.flush()


for cindex, page in enumerate(pages):
    # print('Fetching page ' + str(cindex + 1) + '/' + str(len(pages)))

    threads = page['threads']
    for tindex, thread in enumerate(threads):
        #print('\tFetching thread ' + str(tindex + 1) + '/' + str(len(threads)))
        thread_url = API_URL + 'thread/' + str(thread['no']) + '.json'
        thread_req = get(thread_url)
        if thread_req.status_code != 200:
            print(thread_url)
            raise Exception('Cannot get thread')
        posts = thread_req.json()['posts']

        for pindex, post in enumerate(posts):
            #print('\t\tFetching post ' + str(pindex + 1) + '/'+ str(len(threads)))
            try:
                if post['ext'] != '.webm':
                    #print('\t\t\tNot webm (' + post['ext'] + ')')
                    continue

                file_path = os.path.abspath(os.path.join(FILE_DIR, str(post['tim']) + post['ext']))

                if os.path.isfile(file_path):
                    print('\rPage {0}/{1} Thread {2}/{3} Post {4}/{5} | {6}'.format(
                            str(cindex + 1),
                            len(pages),
                            str(tindex + 1),
                            len(threads),
                            str(pindex + 1),
                            len(posts),
                            'Skipping ' + str(post['tim'])),
                            end=''
                        )
                else:
                    print('\rPage {0}/{1} Thread {2}/{3} Post {4}/{5} | {6}'.format(
                            str(cindex + 1),
                            len(pages),
                            str(tindex + 1),
                            len(threads),
                            str(pindex + 1),
                            len(posts),
                            'Fetching ' + str(post['tim'])),
                            end=''
                        )

                    file_url = CDN_URL + str(post['tim']) + post['ext']
                    file_req = get(file_url)


                    with open(file_path, 'wb') as output:
                        output.write(file_req.content)

                    string = strftime('%Y-%m-%d %H:%M:%S sysadmin imported from /' + BOARD + '/')
                    with open('metadata/' + str(post['tim']) + post['ext'], 'a') as logfile:
                        logfile.write(string + '\n')

            except KeyError:
                pass
