#!/usr/bin/env python3

import os
import pickle
import traceback
import json

### Constants ####

KEY = 0x55
CONFIG_FILE = 'config.bin'

def exception_handler(func, verbose=False):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if verbose:
                traceback.print_exc()
            else:
                print(f"Error: {e}")
    return wrapper

def xor(data):
    return bytes([byte ^ KEY for byte in data])

def config_loader(data_dir):
    config_file = os.path.join(data_dir, CONFIG_FILE)
    if not os.path.exists(config_file):
        return {}
    with open(config_file, 'rb') as file:
        data = file.read()
    data = xor(data)
    data = pickle.loads(data)
    return data

def config_saver(config, data_dir):
    config_file = os.path.join(data_dir, CONFIG_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    config_data = {section: dict(config.items(section)) for section in config.sections()}
    obfuscated_data = xor(pickle.dumps(config_data))
    with open(config_file, 'wb') as file:
        file.write(obfuscated_data)
    with open(os.path.join(data_dir, 'config.ini'), 'w') as file:
        json.dump(config_data, file, indent=4)