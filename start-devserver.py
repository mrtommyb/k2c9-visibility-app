#!/usr/bin/env python
"""Starts the Flask app in debug mode.

Do not use in production.
"""
from tesstvgapp import tvgapp

if __name__ == "__main__":
    tvgapp.debug = True
    tvgapp.run(port=8042, host='0.0.0.0', processes=3)
