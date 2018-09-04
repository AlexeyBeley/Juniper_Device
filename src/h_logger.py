import logging
import pdb

class HLogger(object):
    
    _logger = None
        
    def __new__(cls, name):
        if HLogger._logger is None:
            HLogger._logger = logging.getLogger(name)

        return HLogger._logger
        
        