# Delta PSI

[中文版](./README_zh.md)

## Overview

Delta PSI is a python private set intersection library which implements a 
[KKRT16](https://eprint.iacr.org/2016/799) protocol
based on cuckoo hashing and OT (oblivious transfer).

## Install

Clone this repository, and run command

```
python setup.py install
```

## Usage

Run these two python scripts

```
python psi_server.py
```

and 

```
python psi_client.py
```

you can see the intersection set output in the terminal.

You can change the `words` variable in psi_server.py and psi_client.py 
to change the sets to intersect.

## Note

This repository is in developing, only for learning purpose and 
should not be used in production environment.

## Contact Us

lencyforce@gmail.com