import pdb
from collections import OrderedDict
import traceback

class Parser(object):
    def __init__(self, logger):
        self.logger = logger
    
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
            
            try:
                lst_line[int_src]
            except Exception as inst:
                pdb.set_trace()
                raise Exception("todo:")
            
            if lst_line[int_src] not in dict_ret:
                dict_ret[lst_line[int_src]] = []
                
            dict_ret[lst_line[int_src]].append(lst_line)
        
        return dict_ret