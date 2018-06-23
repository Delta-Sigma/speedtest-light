# Light Command Line Speedtest

A light command line interface for testing internet bandwidth using speedtest.net.

### Very light
Written for python-mini with minimal dependency requirements. [What's python-mini?](https://wiki.openwrt.org/doc/software/python) Which means it will also run perfectly fine with your regular and diet versions of python.

### History
This project is  a fork of sivel/speedtest-cli. It was created because I needed a script to run on my TP-LINK TR741N router. The original speedtest-cli has too many dependencies, and the router does not have that much space.

### Versions
Tested to work with Python 2.7.


#### Usage

    $ speedtest-cli -h
    usage: speedtest-cli [-h] [-q|--quiet]
    
    Command line interface for testing internet bandwidth using speedtest.net.
    --------------------------------------------------------------------------
    https://github.com/Delta-Sigma/speedtest-cli-light

    optional arguments:
      -h, --help       show this help message and exit
      -q, --quiet      Suppress verbose output, only show basic information