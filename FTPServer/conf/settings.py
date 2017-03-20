#!/usr/bin/env python
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ACCOUNT_FILE = '%s/conf/accounts.cfg' % BASE_DIR
USER_HOME = '%s\home' % BASE_DIR
HOST = '0.0.0.0'
PORT = 2121