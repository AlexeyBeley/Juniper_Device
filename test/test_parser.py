import os
import pdb
import sys

sys.path.insert(0, "..")

from src.h_logger import HLogger
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

        if str_line.startswith("alexey@"):
            continue

        if str_line.startswith("{primary"):
            continue

        if str_line.startswith("alexey.beley@"):
            continue

        if not str_line.startswith("set") and \
                not str_line.startswith("deactivate"):
            print(str_line)
            pdb.set_trace()
            raise Exception

        lst_ret.append(str_line)

    return lst_ret


str_folder_configs_path = "../private_files/"


float_counter = 0
for str_file_name in os.listdir(str_folder_configs_path):
    print("Passed:%s" % (str(float_counter * 100 / len(os.listdir(str_folder_configs_path)))) + "%")
    float_counter += 1
    # if (float_counter * 100 / len(os.listdir(str_folder_configs_path))) < 70:
    #   continue

    dev = JuniperBaseDevice()

    print(str_file_name)
    with open(os.path.join(str_folder_configs_path, str_file_name)) as f:
        str_lines = f.read()
        str_lines = str_lines.replace("\r\n", "\n")
        lst_lines = str_lines.split("\n")
        lst_lines = clear_lines(lst_lines)
        lst_src = map(lambda x: x.split(" "), lst_lines)
        dev.init_from_list(lst_src)
