# Light Command Line Speedtest

A light command line interface for testing internet bandwidth using speedtest.net.

Minimal requirements.

This project is  a fork of sivel/speedtest-cli. It was created because I needed a script to run on my TP-LINK TR741N router. The original speedtest-cli has too many dependencies, and the router does not have that much space.

## Versions

Tested to work with Python 2.7.

## Installation


### Github

`pip install git+https://github.com/Delta-Sigma/speedtest-cli-light.git`

or

```shell
git clone https://github.com/Delta-Sigma/speedtest-cli-light.git
python speedtest-cli/setup.py
```

### Just download (just like the way it was)

```shell
wget -O speedtest-cli https://github.com/Delta-Sigma/speedtest-cli-light/raw/master/speedtest_cli.py
chmod +x speedtest-cli
```

or

```shell
curl -o speedtest-cli https://github.com/Delta-Sigma/speedtest-cli-light/raw/master/speedtest_cli.py
chmod +x speedtest-cli
```

## Usage

    $ speedtest-cli -h
    usage: speedtest-cli [-h] [--simple] [--list] [--server SERVER]
                         [--mini MINI]

    Command line interface for testing internet bandwidth using speedtest.net.
    --------------------------------------------------------------------------
    https://github.com/Delta-Sigma/speedtest-cli-light

    optional arguments:
      -h, --help       show this help message and exit
      --simple         Suppress verbose output, only show basic information
      --list           Display a list of speedtest.net servers sorted by distance
      --server SERVER  Specify a server ID to test against
      --mini MINI      URL of the Speedtest Mini server