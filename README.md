# Delta PSI

[中文版](./README_zh.md)

## Overview

Delta PSI is a python private set intersection library which implements a 
[KKRT16](https://eprint.iacr.org/2016/799) protocol
based on cuckoo hashing and OT (oblivious transfer).

## Install

Clone this repository, and run command

```
pip install .
```

## Command

Initialize config file:

```
psi_run init
```

This command will generate a config file in location `config/config.yaml`


Start PSI server:

```
PSI_CONFIG=<CONFIG> psi_run server <address>
```

The `<CONFIG>` means server config file location, and `<address>` means PSI client address.


Start PSI client:

```
PSI_CONFIG=<CONFIG> psi_run client <address>
```

The `<CONFIG>` means client config file location, and `<address>` means PSI server address.

## DEMO

Run these two commands:

```
PSI_CONFIG=config/server.config.yaml psi_run server 127.0.0.1:2345
```

```
PSI_CONFIG=config/client.config.yaml psi_run client 127.0.0.1:1234
```

to start the demo.

For PSI server, the config file is in `config/server.config.yaml`, the input data file is in `server_data.txt` and the output result file is in `server_result.txt`.

For PSI client, the config file is in `config/client.config.yaml`, the input data file is in `client_data.txt` and the output result file is in `client_result.txt`.

## Note

This repository is in developing, only for learning purpose and 
should not be used in production environment.

## Contact Us

lencyforce@gmail.com