import pdb
from collections import OrderedDict
import traceback

from src.h_logger import HLogger

class Parser(object):
    def __init__(self):
        self.logger = HLogger(__name__)
        
    def init_objects_from_list(self, int_index, lst_lines, dict_init_options, **kwargs):
        """
         lst_src = [["","",""],["","",""]]
        """
        dict_ret = OrderedDict()
        dict_src = self.split_list_to_dict(int_index, lst_lines)
        for str_key in dict_src:
            if str_key not in dict_init_options:
                dict_ret[str_key] = dict_src[str_key]
                self.logger.warning("Unknown key: '%s', at: %s "%(str_key, str(traceback.extract_stack())))
                continue
            
            dict_init_options[str_key](int_index+1, dict_src[str_key], **kwargs)
        
        return dict_ret            
        
    def split_list_to_dict(self, int_src, lst_src):
        dict_ret = OrderedDict()
        
        for lst_line in lst_src:
              
            if not lst_line:
                continue
                
            if lst_line == ['']:
                continue
            
            if len(lst_line) <= int_src:
                continue
            
            if lst_line[int_src] not in dict_ret:
                dict_ret[lst_line[int_src]] = []
                
            dict_ret[lst_line[int_src]].append(lst_line)
        
        return dict_ret
        
    def get_objects_by_values(self, dict_src, lst_src, int_limit=0):
        lst_ret = []
        for obj in lst_src:
            for str_key, value in dict_src.items():
                if not hasattr(obj, str_key):
                    break
                
                if getattr(obj, str_key) != value:
                    break
                
            else:
                lst_ret.append(obj)
                if int_limit:
                    if len(lst_ret) == int_limit:
                        break
            
        return lst_ret

        
        
        