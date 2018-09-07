import sys
import pdb

sys.path.insert(0, "..")


from src.h_logger import HLogger
from src.parser import Parser
from src.juniper_base import JuniperBaseDevice

HLogger(__name__)

dev = JuniperBaseDevice()
#with open("mx_s/mx_1.txt") as f:
with open("../private_files/mx_.txt") as f:
    str_lines = f.read()
    str_lines = str_lines.replace("\r\n", "\n")
    lst_lines = str_lines.split("\n")
    lst_src = map(lambda x: x.split(" "), lst_lines)
    dev.init_from_list(lst_src)
