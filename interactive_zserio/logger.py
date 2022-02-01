import sys
from datetime import datetime

class Logger:
    @staticmethod
    def log(*args):
        if LOGGING_ENABLED:
            print(datetime.now(), *args, file=sys.stderr)

LOGGING_ENABLED=True
