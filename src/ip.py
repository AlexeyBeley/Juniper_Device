import pdb

from enum import Enum


class IP:
    def __init__(self):
        self.logger = None
    
    def _log(self, str_src):
        if self.logger:
            self.logger.error(str_src)
            
    def init_address(self, str_address, **kwargs):
        if "logger" in kwargs:
            self.logger = kwargs["logger"]
            
        if "." in str_address:
            return self.init_address_ipv4_doted(str_address, **kwargs)
        

        str_log = "Can't init address %s, %s"%(str_address, str(kwargs))
        self._log(str_log)
        raise Exception(str_log)
    
    def init_address_ipv4_doted(self, str_src, **kwargs):
        self.type = IP.Types.IPV4
        str_mask = None
        int_mask = None
        
        if "str_mask" in kwargs:
            pdb.set_trace()
        
        if "int_mask" in kwargs:
            pdb.set_trace()
            
        if "/" in str_src:
            if not(str_mask is None) or not(int_mask is None):
                raise Exception
                
            str_address, str_mask = str_src.split("/")
            if not IP.check_ip_validity(str_address):
                raise Exception
            
            if not IP.check_mask_v4_validity(str_mask):
                raise Exception
    
    @staticmethod
    def check_ipv4_validity(str_src):
        lst_src = str_src.split(".")
        if len(lst_src) != 4:
            return False
        
        try:
            for str_oct in lst_src:
                int_oct = int(str_oct)
                if int_oct < 0 or int_oct > 255:
                    return False
        except Exception:
            return False
        
        return True
            
    @staticmethod
    def check_ip_validity(str_src):
        if "." in str_src:
            return IP.check_ipv4_validity(str_src)
        
        raise Exception
    
    @staticmethod
    def check_mask_v4_validity(str_src):
        if str_src.isdigit():
            int_src = int(str_src)
            if int_src < 0 or int_src > 32:
                return False
            
            return True
            
        raise Exception
        
    class Types(Enum):
        IPV4 = "IPv4"
        IPV6 = "IPv6"
        
        
        
        