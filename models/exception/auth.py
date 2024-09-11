#!/usr/bin/env python3

class AuthenticationError(Exception):
    def __init__(self, message, err_code):
        self.message = message
        self.err_code = err_code

    def __str__(self):
        return f"AuthenticationError: {self.message}"

