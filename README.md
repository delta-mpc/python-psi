# Delta PSI

Delta PSI is a private set intersection library which implements a 
[KKRT16](https://eprint.iacr.org/2016/799) protocol
based on cuckoo hashing and OT (oblivious transfer).

## Install

Clone this repository, and run command

```
python setup.py install
```

## Usage

Run command

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