#!/usr/bin/env python3
import os, sys, binascii
[print(binascii.unhexlify(d)) for d in os.listdir(sys.argv[1])]
