import sys
import os
import pdb

sys.path.insert(0, "..")


from src.h_logger import HLogger
from src.parser import Parser
from src.juniper_base import JuniperBaseDevice

HLogger(__name__)

def clear_lines(lst_src):
    lst_ret = []
    for str_line in lst_src:
        if not str_line: 
            continue
        
        if str_line.startswith("incaptom@"):
            continue
            
        if str_line.startswith("show configuration"):
            continue
        
        if str_line.startswith("{master"):
            continue
            
        if not str_line.startswith("set") and\
           not str_line.startswith("deactivate"):
           pdb.set_trace()
        
        lst_ret.append(str_line)
    
    return lst_ret

str_folder_configs_path = "../private_files/"
for str_file_name in os.listdir(str_folder_configs_path):
    dev = JuniperBaseDevice()
    print(str_file_name)
    with open(os.path.join(str_folder_configs_path, str_file_name)) as f:
        str_lines = f.read()
        str_lines = str_lines.replace("\r\n", "\n")
        lst_lines = str_lines.split("\n")
        lst_lines = clear_lines(lst_lines)
        lst_src = map(lambda x: x.split(" "), lst_lines)
        dev.init_from_list(lst_src)
