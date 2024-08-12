#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import sys
import datetime

def log_info(msg):
    sys.stderr.write(f'INFO {datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")}: {msg}\n')

def log_err(msg):
    sys.stderr.write(f'ERROR {datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")}: {msg}\n')

def log_warning(msg):
    sys.stderr.write(f'WARNING {datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")}: {msg}\n')

def log_start(msg):
    sys.stderr.write(f'START {datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")}: {msg}\n')

def log_end(msg):
    sys.stderr.write(f'END {datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")}: {msg}\n')
