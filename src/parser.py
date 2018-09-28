import pdb
from collections import OrderedDict
import traceback

from src.h_logger import HLogger


class Parser(object):
    def __init__(self):
        self.logger = HLogger(__name__)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return True

    def init_objects_from_list_base(self, int_index, lst_lines, dict_init_options, **kwargs):
        """
         lst_src = [["","",""],["","",""]]
        """
        dict_ret = OrderedDict()
        dict_src = self.split_list_to_dict(int_index, lst_lines)
        for str_key in dict_src:
            if str_key not in dict_init_options:
                dict_ret[str_key] = dict_src[str_key]
                self.logger.warning("Unknown key: '%s', at: %s " % (str_key, str(traceback.extract_stack())))
                continue

            dict_init_options[str_key](int_index + 1, dict_src[str_key], **kwargs)

        return dict_ret

    def init_objects_from_list(self, int_index, lst_lines, dict_init_options, **kwargs):
        """
         lst_src = [["","",""],["","",""]] list of space split configuration lines
         "func_key" = sorting function to select the order
        """
        if "func_key" in kwargs:
            func_key = kwargs["func_key"]
        else:
            def func_key(x):
                return 0

        dict_ret = OrderedDict()
        dict_src = self.split_list_to_dict(int_index, lst_lines)

        lst_ordered_src = sorted(list(dict_src.keys()), key=func_key)

        int_index += 1

        for str_key in lst_ordered_src:
            if str_key not in dict_init_options:
                dict_ret[str_key] = dict_src[str_key]
                self.logger.warning("Unknown key: '%s', at: %s " % (str_key, str(traceback.extract_stack())))
                continue

            dict_init_options[str_key](int_index, dict_src[str_key], **kwargs)

        return dict_ret

    # todo:check
    def split_list_to_dict_recursive(self, int_src, lst_src):
        dict_ret = self.split_list_to_dict(int_src, lst_src)
        for str_key, lst_lines in dict_ret.items():
            ret = self.split_list_to_dict_recursive(int_src + 1, lst_lines)

            if ret == OrderedDict():
                dict_ret[str_key] = lst_lines
            else:
                dict_ret[str_key] = ret

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

    @staticmethod
    def get_objects_by_values(dict_src, lst_src, int_limit=0):
        """

        :param dict_src: Search values
        :param lst_src: List of objects to search in
        :param int_limit: Maximum count of return values
        :return: List of found values
        """
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

    @staticmethod
    def merge_objects_(object_self, object_other, object_default, dict_merge_options, lst_ignore=["lst_src"]):
        if object_self.__class__ != object_other.__class__:
            raise Exception

        for str_key, attr_other in object_other.__dict__.items():
            if str_key in lst_ignore:
                continue

            if hasattr(object_default, str_key):
                if not hasattr(object_self, str_key):
                    raise Exception

                attr_default = getattr(object_default, str_key)
                attr_self = getattr(object_self, str_key)

                if attr_other == attr_default:
                    continue
                if str_key in dict_merge_options:
                    dict_merge_options[str_key](object_other)
                else:
                    pdb.set_trace()
                    raise Exception
            else:
                if hasattr(object_self, str_key):
                    attr_self = getattr(object_self, str_key)

                    if attr_other == attr_self:
                        continue

                    if str_key in dict_merge_options:
                        dict_merge_options[str_key](object_other)
                    else:
                        pdb.set_trace()
                        raise Exception
                else:
                    setattr(object_self, str_key, attr_other)
                    continue
