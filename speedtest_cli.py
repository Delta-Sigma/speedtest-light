#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Matt Martz
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import print_function

try:
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request

import math
import time
import os
import sys
import threading
import binascii
import re
from xml.dom import minidom as DOM

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from urlparse import parse_qs
except ImportError:
    try:
        from urllib.parse import parse_qs
    except ImportError:
        from cgi import parse_qs

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from optparse import OptionParser


def distance(origin, destination):
    """Determine distance between 2 sets of [lat,lon] in km"""
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlon / 2)
         * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c
    return d


class FileGetter(threading.Thread):
    def __init__(self, url, start):
        self.url = url
        self.result = None
        self.starttime = start
        threading.Thread.__init__(self)

    def get_result(self):
        return self.result

    def run(self):
        try:
            if (time.time() - self.starttime) <= 10:
                f = urlopen(self.url)
                self.result = 0
                while 1:
                    contents = f.read(10240)
                    if contents:
                        self.result += len(contents)
                    else:
                        break
                f.close()
            else:
                self.result = 0
        except IOError:
            self.result = 0


def downloadSpeed(files, quiet=False):
    start = time.time()

    def producer(q, files):
        for file in files:
            thread = FileGetter(file, start)
            thread.start()
            q.put(thread, True)
            if not quiet:
                sys.stdout.write('.')
                sys.stdout.flush()

    finished = []

    def consumer(q, total_files):
        while len(finished) < total_files:
            thread = q.get(True)
            thread.join()
            finished.append(thread.result)
            thread.result = 0

    q = Queue(6)
    start = time.time()
    prod_thread = threading.Thread(target=producer, args=(q, files))
    cons_thread = threading.Thread(target=consumer, args=(q, len(files)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    return (sum(finished)/(time.time()-start))


class FilePutter(threading.Thread):
    def __init__(self, url, start, size):
        self.url = url
        data = binascii.hexlify(os.urandom(int(size)-9)).decode()
        self.data = ('content1=%s' % data[0:int(size)-9]).encode()
        del data
        self.result = None
        self.starttime = start
        threading.Thread.__init__(self)

    def get_result(self):
        return self.result

    def run(self):
        try:
            if (time.time() - self.starttime) <= 10:
                f = urlopen(self.url, self.data)
                contents = f.read()
                f.close()
                self.result = len(self.data)
            else:
                self.result = 0
        except IOError:
            self.result = 0


def uploadSpeed(url, sizes, quiet=False):
    start = time.time()

    def producer(q, sizes):
        for size in sizes:
            thread = FilePutter(url, start, size)
            thread.start()
            q.put(thread, True)
            if not quiet:
                sys.stdout.write('.')
                sys.stdout.flush()

    finished = []

    def consumer(q, total_sizes):
        while len(finished) < total_sizes:
            thread = q.get(True)
            thread.join()
            finished.append(thread.result)
            thread.result = 0

    q = Queue(6)
    start = time.time()
    # prod_thread = _thread.start_new_thread(producer, (q,sizes))
    prod_thread = threading.Thread(target=producer, args=(q, sizes))
    # cons_thread = _thread.start_new_thread(consumer, (q,len(sizes)))
    cons_thread = threading.Thread(target=consumer, args=(q, len(sizes)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    return (sum(finished)/(time.time()-start))


def getAttributesByTagName(dom, tagName):
    elem = dom.getElementsByTagName(tagName)[0]
    return dict(list(elem.attributes.items()))


def getConfig():
    """Download the speedtest.net configuration and return only the data
    we are interested in
    """

    uh = urlopen('http://www.speedtest.net/speedtest-config.php')
    configxml = uh.read()
    if int(uh.code) != 200:
        return None
    uh.close()
    root = DOM.parseString(configxml)
    config = {
        'client': getAttributesByTagName(root, 'client'),
        'times': getAttributesByTagName(root, 'times'),
        'download': getAttributesByTagName(root, 'download'),
        'upload': getAttributesByTagName(root, 'upload')}

    del root
    return config


def closestServers(client, all=False):
    """Determine the 5 closest speedtest.net servers based on geographic
    distance
    """

    uh = urlopen('http://www.speedtest.net/speedtest-servers.php')
    serversxml = uh.read()
    if int(uh.code) != 200:
        return None
    uh.close()
    root = DOM.parseString(serversxml)
    servers = {}
    for server in root.getElementsByTagName('server'):
        attrib = dict(list(server.attributes.items()))
        d = distance([float(client['lat']), float(client['lon'])],
                     [float(attrib.get('lat')), float(attrib.get('lon'))])
        attrib['d'] = d
        if d not in servers:
            servers[d] = [attrib]
        else:
            servers[d].append(attrib)
    del root

    closest = []
    for d in sorted(servers.keys()):
        for s in servers[d]:
            closest.append(s)
            if len(closest) == 5 and not all:
                break
        else:
            continue
        break

    del servers
    return closest


def getBestServer(servers):
    """Perform a speedtest.net "ping" to determine which speedtest.net
    server has the lowest latency
    """
    results = {}
    for server in servers:
        cum = 0
        url = os.path.dirname(server['url'])
        for i in range(0, 3):
            uh = urlopen('%s/latency.txt' % url)
            start = time.time()
            text = uh.read().strip()
            total = time.time() - start
            if int(uh.code) == 200 and text == 'test=test'.encode():
                cum += total
            else:
                cum += 3600
            uh.close()
        avg = round((cum / 3) * 1000000, 3)
        results[avg] = server

    fastest = sorted(results.keys())[0]
    best = results[fastest]
    best['latency'] = fastest

    return best


def speedtest():
    """Run the full speedtest.net test"""

    description = (
        'Light version of command line interface for testing internet bandwidth using '
        'speedtest.net.\n'
        '------------------------------------------------------------'
        '--------------\n'
        'https://github.com/Delta-Sigma/speedtest-cli-light')

    parser = OptionParser(description=description)
    try:
        parser.add_argument = parser.add_option
    except AttributeError:
        pass
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Suppress verbose output, only show basic '
                             'information')

    options = parser.parse_args()
    if isinstance(options, tuple):
        args = options[0]
    else:
        args = options
    del options

    if not args.quiet:
        print('Retrieving speedtest.net configuration...')
    config = getConfig()

    if not args.quiet:
        print('Retrieving speedtest.net server list...')
    servers = closestServers(config['client'])

    if not args.quiet:
        print('Testing from %(isp)s (%(ip)s)...' % config['client'])

    if not args.quiet:
        print('Selecting best server based on ping...')
    best = getBestServer(servers)

    if not args.quiet:
        print('Hosted by %(sponsor)s (%(name)s) [%(d)0.2f km]: '
               '%(latency)s ms' % best)
    else:
        print('Ping: %(latency)s ms' % best)

    sizes = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
    urls = []
    for size in sizes:
        for i in range(0, 4):
            urls.append('%s/random%sx%s.jpg' %
                        (os.path.dirname(best['url']), size, size))
    if not args.quiet:
        print('Testing download speed', end='')
    dlspeed = downloadSpeed(urls, args.quiet)
    if not args.quiet:
        print()
    print('Download: %0.2f Mbit/s' % ((dlspeed / 1000 / 1000) * 8))

    sizesizes = [int(.25 * 1000 * 1000), int(.5 * 1000 * 1000)]
    sizes = []
    for size in sizesizes:
        for i in range(0, 25):
            sizes.append(size)
    if not args.quiet:
        print('Testing upload speed', end='')
    ulspeed = uploadSpeed(best['url'], sizes, args.quiet)
    if not args.quiet:
        print()
    print('Upload: %0.2f Mbit/s' % ((ulspeed / 1000 / 1000) * 8))

def main():
    try:
        speedtest()
    except KeyboardInterrupt:
        print('\nCancelling...')

if __name__ == '__main__':
    main()
