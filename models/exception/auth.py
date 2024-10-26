#!/usr/bin/env python3

import resources.strings as strings
class AuthenticationError(Exception):
    def __init__(self, message, err_code):
        self.message = message
        self.err_code = err_code

    def __str__(self):
        return f"{strings.EXC_AUTH_ERROR}: {self.message}"

