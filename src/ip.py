import pdb
import re

from enum import Enum


class IP:
    """
    Class for network engineers usage
    """
    def __init__(self):
        self.type = None
        self.str_int_mask = None
        self.int_mask = None
        self.str_mask = None
        self.str_address = None
        self.logger = None
    
    @property
    def str_int_mask(self):
        return self._str_int_mask
    
    @str_int_mask.setter
    def str_int_mask(self, value):
        if value is None:
            self._str_int_mask = None
            return
        
        if self.type == IP.Types.IPV4:
            if not IP.check_str_int_mask_v4_validity(value):
                raise Exception
        elif self.type == IP.Types.IPV6:
            if not IP.check_str_int_mask_v6_validity(value):
                raise Exception
        else:
            raise Exception
        
        self._str_int_mask = value
    
    @property
    def int_mask(self):
        return self._int_mask
    
    @int_mask.setter
    def int_mask(self, value):
        if value is None:
            self._int_mask = None
            return
            
        if self.type == IP.Types.IPV4:
            if not IP.check_int_mask_v4_validity(value):
                raise Exception
        elif self.type == IP.Types.IPV6:
            if not IP.check_int_mask_v6_validity(value):
                raise Exception
        else:
            raise Exception
        
        self._int_mask = value
    
    @property
    def str_mask(self):
        return self._str_mask
    
    @str_mask.setter
    def str_mask(self, value):
        if value is None:
            self._str_mask = None
            return
            
        pdb.set_trace()
        if value not in [True, False]:
            raise Exception
        
        self._str_mask = value
    
    @property
    def str_address(self):
        return self._str_address
    
    @str_address.setter
    def str_address(self, value):
        if value is None:
            self._str_address = None
            return
            
        if self.type == IP.Types.IPV4:
            if not IP.check_ipv4_validity(value):
                raise Exception
        elif self.type == IP.Types.IPV6:
            if not IP.check_ipv6_validity(value):
                raise Exception
        else:
            raise Exception
        
        self._str_address = value
    
    def _log(self, str_src):
        if self.logger:
            self.logger.error(str_src)
            
    def init_host(self, str_address, **kwargs):
        return self.init_address(str_address, int_mask = 32)
        
    def init_address(self, str_src, **kwargs):
        if "logger" in kwargs:
            self.logger = kwargs["logger"]
            
        if "." in str_src:
            self.type = IP.Types.IPV4
        
        if ":" in str_src:
            self.type = IP.Types.IPV6
        
        self.str_mask = None
        self.str_int_mask = None
        self.int_mask = None
        
        if "str_mask" in kwargs:
            pdb.set_trace()
        
        if "int_mask" in kwargs:
            if "/" in str_src:
                raise Exception
            self.int_mask = kwargs["int_mask"]
            
        if "/" in str_src:
            if (self.str_mask is not None) or\
            (self.int_mask is not None) or\
            (self.str_int_mask is not None):
                raise Exception
                
            self.str_address, str_mask = str_src.split("/")
            
            if str_mask.isdigit():
                self.str_int_mask = str_mask
            else:
                self.str_mask = str_mask
        else:
            self.str_address = str_src
                
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
    def convert_short_to_long_ipv6(str_src):
        lst_ret = []
        lst_src = str_src.split(":")
        for str_group in lst_src:
            if str_group:
                if len(str_group) < 4:
                    str_group = "0" * (4-len(str_group)) + str_group
                lst_ret.append(str_group)
            else:
                lst_ret += ["0000" for x in range((9 - len(lst_src)))]
                
        return lst_ret
        
    @staticmethod
    def check_ipv6_validity(str_src):
        lst_long_address = IP.convert_short_to_long_ipv6(str_src)
        if len(lst_long_address) != 8:
            return False
        
        try:
            for str_part in lst_long_address:
                pattern = re.compile("^[a-f0-9]{4}$")
                match_part = re.match(pattern, str_part)
                if not match_part:
                    return False
                
        except Exception:
            return False
        
        return True
        
    @staticmethod
    def check_ip_validity(str_src):
        if "." in str_src:
            return IP.check_ipv4_validity(str_src)
        
        if ":" in str_src:
            return IP.check_ipv6_validity(str_src)
        
        
        raise Exception
    
    @staticmethod
    def check_str_int_mask_v4_validity(str_src):
        if type(str_src) is not str:
            return False
            
        if not str_src.isdigit():
            return False
            
        return IP.check_int_mask_v4_validity(int(str_src))
    
    @staticmethod
    def check_str_int_mask_v6_validity(str_src):
        if type(str_src) is not str:
            return False
            
        if not str_src.isdigit():
            return False
            
        return IP.check_int_mask_v6_validity(int(str_src))
    
    @staticmethod
    def check_int_mask_v4_validity(int_src):
        if type(int_src) is not int:
            return False
            
        if int_src < 0 or int_src > 32:
            return False
        
        return True
    
    @staticmethod
    def check_int_mask_v6_validity(int_src):
        if type(int_src) is not int:
            return False
            
        if int_src < 0 or int_src > 128:
            return False
        
        return True
    
    class Types(Enum):
        IPV4 = "IPv4"
        IPV6 = "IPv6"
        
        
        
        