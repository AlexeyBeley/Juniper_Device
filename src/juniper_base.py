import pdb
import sys
import os
import re

str_top_path = os.path.realpath(os.path.join(os.path.join(os.path.join(os.path.realpath(__file__), ".."), ".."), ".."))


sys.path.insert(0, os.path.realpath(os.path.join(os.path.join(str_top_path, "IP"), "src")))


from collections import OrderedDict
from enum import Enum


from ip import IP
from src.parser import Parser
from src.h_logger import HLogger


class ConfigurationElement(object):
    def __init__(self):
        self.value = None

        self._bool_active = None
        self.bool_active = True

        self.lst_src = None
        self.parser = Parser()

    @property
    def bool_active(self):
        return self._bool_active

    @bool_active.setter
    def bool_active(self, value):
        if value not in [True, False]:
            raise Exception

        self._bool_active = value

    @staticmethod
    def generate_attr_name_from_config_name(str_src):
        str_src = str_src.lower()
        while "-" in str_src:
            str_src = str_src.replace("-", "_")
        str_src = str_src.replace("-", "_")
        return str_src

    @staticmethod
    def generate_class_name_from_config_name(str_src):
        str_ret = str_src[0].upper()
        i = 1

        while i < len(str_src):
            if str_src[i] == "-":

                if i == len(str_src) - 1:
                    raise Exception
                str_ret += str_src[i + 1].upper()
                i += 1
            else:
                str_ret += str_src[i]

            i += 1

        return str_ret

    @staticmethod
    def generate_configuration_elemenet_class(str_name):
        def get_attr_name():
            return ConfigurationElement.generate_attr_name_from_config_name(str_name)

        @ConfigurationElement.preprocess_object_init
        def init_from_list(self, int_index, lst_src, **kwargs):
            self.lst_src = lst_src

        cls_ret = type(ConfigurationElement.generate_class_name_from_config_name(str_name), (ConfigurationElement,),
                       {"get_attr_name": get_attr_name, "init_from_list": init_from_list})
        return cls_ret

    @staticmethod
    def init_configuration_element_default_from_list(int_index, lst_src, **kwargs):
        str_init_class_name = ConfigurationElement.generate_class_name_from_config_name(
            lst_src[0][int_index - 1])

        for str_class_attrs in dir(kwargs["obj_caller"].__class__):
            if str_class_attrs == str_init_class_name:
                cls_to_init = getattr(kwargs["obj_caller"].__class__, str_class_attrs)
                break
        else:
            cls_to_init = ConfigurationElement.generate_configuration_elemenet_class(lst_src[0][int_index - 1])
            setattr(kwargs["obj_caller"].__class__, cls_to_init.__name__, cls_to_init)

        obj_attr = cls_to_init()
        obj_attr.init_from_list(int_index, lst_src, **kwargs)
        return obj_attr

    @staticmethod
    def init_default_from_list(obj_caller):
        def generate_init_element(int_index, lst_src, obj_caller=obj_caller, **kwargs):
            obj_ret = ConfigurationElement.init_configuration_element_default_from_list(int_index, lst_src,
                                                                                        obj_caller=obj_caller, **kwargs)
            setattr(obj_caller, obj_ret.__class__.get_attr_name(), obj_ret)

        return generate_init_element

    @staticmethod
    def init_default_bool_from_list(obj_caller_src):
        """obj_caller is the one which has subclasses in it"""

        def generate_init_bool_element(int_index, lst_src, obj_caller=obj_caller_src, **kwargs):
            obj_ret = ConfigurationElement.init_configuration_element_default_from_list(int_index, lst_src,
                                                                                        obj_caller=obj_caller, **kwargs)
            setattr(obj_caller, obj_ret.__class__.get_attr_name(), obj_ret)
            obj_ret.value = True

        return generate_init_bool_element

    def init_from_list(self, int_index, lst_src, **kwargs):
        raise NotImplementedError("todo:")

    @staticmethod
    def preprocess_object_init(func_src):
        def func_ret(self, int_index, lst_src, **kwargs):
            lst_src_new = []

            for i in range(len(lst_src)):
                lst_line = lst_src[i]
                # deactivate
                if lst_line[0] != "set":
                    if lst_line[0] != "deactivate":
                        pdb.set_trace()
                        raise Exception

                    if len(lst_line) == int_index:
                        self.bool_active = False
                        if len(lst_src) - 1 != i:
                            raise Exception
                        continue

                # apply_groups
                if "apply-groups" in lst_line:
                    pass

                if len(lst_line) > int_index:
                    if lst_line[int_index] == "apply-groups":
                        lst_grp = self.parser.get_objects_by_values({"name": lst_line[int_index + 1]},
                                                                    kwargs["lst_groups"], int_limit=1)
                        if not lst_grp:
                            raise Exception

                        lst_lines_applied = ConfigurationElement.apply_group(int_index, lst_src, lst_grp[0])

                        for lst_line_applied in lst_lines_applied:
                            if lst_line_applied not in lst_src_new:
                                lst_src_new.append(lst_line_applied)

                        # remove the apply-group line
                        continue

                if lst_line not in lst_src_new:
                    lst_src_new.append(lst_line)

            func_src(self, int_index, lst_src_new, **kwargs)

        return func_ret

    @staticmethod
    def apply_group(int_index, lst_src, grp_src):
        lst_ret = []

        for lst_grp_line in grp_src.lst_src:
            for lst_line in lst_src:
                if lst_line[int_index] == 'apply-groups':
                    continue
                lst_line_new = ConfigurationElement.apply_group_line(int_index, lst_line, lst_grp_line)
                if not lst_line_new:
                    continue

                if lst_line_new in lst_ret:
                    continue

                if lst_line_new in lst_src:
                    continue

                lst_ret.append(lst_line_new)

        return lst_ret

    @staticmethod
    def apply_group_line(int_index, lst_str_config, lst_str_grp):
        lst_ret = []
        int_index_config = 1
        int_index_grp = 3

        while int_index_grp < len(lst_str_grp):
            str_config = lst_str_config[int_index_config]
            str_grp = lst_str_grp[int_index_grp]

            if "<" in lst_str_grp[int_index_grp]:
                bool_ret = ConfigurationElement.check_regex_config(str_config, str_grp)
                if not bool_ret:
                    if str_grp == str_config:
                        raise Exception
                    return []

                str_grp = str_config

            if str_config != str_grp:
                if int_index < int_index_grp:
                    for str_grp_cfg in lst_str_grp[int_index_grp:]:
                        if "<" in str_grp_cfg and ">" in str_grp_cfg:
                            pdb.set_trace()
                            raise Exception
                    return lst_str_config[:int_index_config] + lst_str_grp[int_index_grp:]

                pdb.set_trace()
                return []

            int_index_grp += 1
            int_index_config += 1

        return lst_ret

    @staticmethod
    def check_regex_config(str_config, str_grp):
        if str_grp[0] != "<":
            raise Exception

        if str_grp[-1] != ">":
            raise Exception

        if str_grp == "<*>":
            return True

        str_grp = str_grp.strip("<>")

        result_search = re.search(str_grp, str_config)
        if not result_search:
            return False

        return True

    @classmethod
    def get_attr_name(cls):
        """

        :return: string: a name for my class to be set as attr name
        """
        str_ret = cls.__name__[0].lower()
        for i in range(1, len(cls.__name__)):
            str_current_char = cls.__name__[i]
            if str_current_char.istitle():
                str_ret += "_" + str_current_char.lower()
            else:
                str_ret += str_current_char.lower()

        return str_ret

    def merge(self, object_other, lst_ignore=None, dict_merge_options=None):
        if dict_merge_options is None:
            dict_merge_options = {}

        if lst_ignore is None:
            lst_ignore = ["lst_src"]

        self.merge_base(object_other, lst_ignore=lst_ignore, dict_merge_options=dict_merge_options)

    def merge_base(self, object_other, lst_ignore=None, dict_merge_options=None):
        if dict_merge_options is None:
            dict_merge_options = {}

        if lst_ignore is None:
            lst_ignore = ["lst_src"]

        object_default = self.__class__()
        if self.__class__ != object_other.__class__:
            raise Exception

        for str_key, attr_other in object_other.__dict__.items():
            if str_key in lst_ignore:
                continue

            if not hasattr(self, str_key):
                setattr(self, str_key, attr_other)
                continue

            attr_self = getattr(self, str_key)

            if hasattr(object_default, str_key):
                attr_default = getattr(object_default, str_key)

                if attr_other == attr_default:
                    continue

                if attr_self == attr_default:
                    setattr(self, str_key, attr_other)
                    continue
            else:
                if attr_other == attr_self:
                    continue

            if str_key in dict_merge_options:
                dict_merge_options[str_key](object_other)
            else:
                self.merge_attr(object_other, str_key)

    def merge_attr_base(self, obj_other, str_attr_name):
        attr_self = getattr(self, str_attr_name)
        attr_self.merge(getattr(obj_other, str_attr_name))

    def merge_attr(self, obj_other, str_attr_name):
        return self.merge_attr_base(obj_other, str_attr_name)


class Interface(ConfigurationElement):
    def __init__(self):
        super().__init__()
        self.name = None
        self.parser = Parser()
        self.units = []
        self.bool_active = True
        self.bool_enabled = True
        self.lst_src = None

    @ConfigurationElement.preprocess_object_init
    def init_from_list(self, int_index, lst_src, **kwargs):
        self.lst_src = lst_src
        self.name = lst_src[0][int_index - 1]

        dict_init_options = self.get_dict_init_options()

        def func_key(str_attr):
            return 0

        dict_ret = self.parser.init_objects_from_list(
            int_index, lst_src, dict_init_options, func_key=func_key, **kwargs)

        if dict_ret:
            for x in dict_ret:
                print("###" + x)
            pdb.set_trace()

    def get_dict_init_options(self):
        # Each interface can edit this option to manipulate the inited objects

        dict_ret = {
            "unit": self.init_unit_from_list,
            "vlan-tagging": ConfigurationElement.init_default_bool_from_list(self),
            "description": ConfigurationElement.init_default_from_list(self),
            "ether-options": ConfigurationElement.init_default_from_list(self),
            "gigether-options": ConfigurationElement.init_default_from_list(self),
            "no-gratuitous-arp-reply": ConfigurationElement.init_default_bool_from_list(self),
            "no-gratuitous-arp-request": ConfigurationElement.init_default_bool_from_list(self),
            "aggregated-ether-options": ConfigurationElement.init_default_from_list(self),
            "disable": self.init_disable_from_list,
            "enable": self.init_enable_from_list,
            "speed": ConfigurationElement.init_default_from_list(self),
            "link-mode": ConfigurationElement.init_default_from_list(self),
            "redundant-ether-options": ConfigurationElement.init_default_from_list(self),
            "fabric-options": ConfigurationElement.init_default_from_list(self),
            "apply-groups": self.init_apply_groups_from_list,
            "gratuitous-arp-reply": ConfigurationElement.init_default_bool_from_list(self),
        }
        return dict_ret

    def init_apply_groups_from_list(self, int_index, lst_src, **kwargs):
        raise Exception("Shouldn't reach here!")

    def init_disable_from_list(self, int_index, lst_src, **kwargs):
        if len(lst_src) != 1:
            raise Exception

        if lst_src[0][0] != "set":
            raise Exception

        self.bool_enabled = False

    def init_enable_from_list(self, int_index, lst_src, **kwargs):
        if len(lst_src) != 1:
            raise Exception

        if lst_src[0][0] != "set":
            raise Exception

        self.bool_enabled = True

    def init_unit_from_list(self, int_index, lst_src, **kwargs):
        dict_ret = self.parser.split_list_to_dict(int_index, lst_src)
        for str_unit_name, lst_lines in dict_ret.items():
            unit = Interface.Unit()
            unit.init_from_list(int_index + 1, lst_lines, **kwargs)
            self.units.append(unit)

    def merge(self, object_other, lst_ignore=None, dict_merge_options=None):
        if dict_merge_options is None:
            dict_merge_options = {}

        if lst_ignore is None:
            lst_ignore = ["lst_src"]

        dict_merge_options["name"] = self.merge_name
        dict_merge_options["units"] = self.merge_unit

        self.merge_base(object_other, lst_ignore=lst_ignore, dict_merge_options=dict_merge_options)

    def merge_unit(self, obj_other):
        for unit_other in obj_other.units:
            lst_self_units = self.parser.get_objects_by_values({"name": unit_other.name}, self.units, int_limit=1)
            if not lst_self_units:
                self.units.append(unit_other)
            else:
                lst_self_units[0].merge(unit_other)

    def merge_name(self, obj_other):
        if self.name != obj_other.name:
            raise Exception

    class AggregatedEtherOptions(ConfigurationElement):
        def __init__(self):
            super().__init__()
            self.lacp = None
            self.bool_active = False
            self.parser = Parser()

        @ConfigurationElement.preprocess_object_init
        def init_from_list(self, int_index, lst_src, **kwargs):
            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src,
                {
                    "lacp": ConfigurationElement.init_default_from_list(self),
                    "link-speed": ConfigurationElement.init_default_from_list(self),
                },
                **kwargs)

            if dict_ret:
                pdb.set_trace()

        class Lacp(ConfigurationElement):
            def __init__(self):
                super().__init__()
                self.lacp = None
                self.bool_active = False
                self.parser = Parser()

            @ConfigurationElement.preprocess_object_init
            def init_from_list(self, int_index, lst_src, **kwargs):
                dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src,
                    {
                        "active": ConfigurationElement.init_default_bool_from_list(self),
                        "periodic": ConfigurationElement.init_default_from_list(self),
                        "force-up": ConfigurationElement.init_default_from_list(self),
                    },
                    **kwargs)

                if dict_ret:
                    pdb.set_trace()

    class DescriptionValue:
        def __init__(self):
            self.str_value = None
            self.bool_active = False

        @ConfigurationElement.preprocess_object_init
        def init_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception
            self.str_value = lst_src[0][int_index]

    class GigetherOptions(ConfigurationElement):
        def __init__(self):
            super().__init__()
            self.bool_active = True
            self.parser = Parser()

        @ConfigurationElement.preprocess_object_init
        def init_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception

            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src, {
                    "802.3ad": self.init_802_3ad_from_list,
                    "no-auto-negotiation": ConfigurationElement.init_default_bool_from_list(self),
                    "redundant-parent": ConfigurationElement.init_default_from_list(self),
                },
                **kwargs)

            if dict_ret:
                pdb.set_trace()

        def init_802_3ad_from_list(self, int_index, lst_src, **kwargs):
            self.protocol_802dot3ad = Interface.GigetherOptions.Protocol802dot3ad()
            self.protocol_802dot3ad.init_from_list(int_index, lst_src, **kwargs)

        class Protocol802dot3ad:
            def __init__(self):
                self.ae_interface = None
                self.logger = HLogger(__name__)
                self.parser = Parser()

            @ConfigurationElement.preprocess_object_init
            def init_from_list(self, int_index, lst_src, **kwargs):
                if len(lst_src) != 1:
                    raise Exception

                inter_ret = self.parser.get_objects_by_values({"name": lst_src[0][int_index]}, kwargs["lst_interfaces"],
                                                              int_limit=1)
                if not inter_ret:
                    self.logger.warning("Can't find interface '%s', at: %s " %
                                        (lst_src[0][int_index], " ".join(lst_src[0])))

                self.ae_interface = inter_ret

    class Unit(ConfigurationElement):
        def __init__(self):
            super().__init__()
            self.name = None
            self.vlan_id = None
            self.bool_enabled = True
            self.parser = Parser()
            self.dict_vars_vals = {}

        @ConfigurationElement.preprocess_object_init
        def init_from_list(self, int_index, lst_src, **kwargs):
            self.lst_src = lst_src
            self.name = lst_src[0][int_index - 1]
            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src, {
                    "clear-dont-fragment-bit": self.init_clear_dont_fragment_bit_from_list,
                    "description": ConfigurationElement.init_default_from_list(self),
                    "tunnel": self.init_tunnel_from_list,
                    "family": self.init_family_from_list,
                    "vlan-id": self.init_vlan_id_from_list,
                    "disable": self.init_disable_from_list,
                    "encapsulation": ConfigurationElement.init_default_from_list(self),
                    "peer-unit": ConfigurationElement.init_default_from_list(self),
                    "mac": ConfigurationElement.init_default_from_list(self),
                    "arp-resp": ConfigurationElement.init_default_from_list(self),
                },
                **kwargs)
            if dict_ret:
                pdb.set_trace()

        def init_disable_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception

            self.bool_enabled = False

        def init_vlan_id_from_list(self, int_index, lst_src, **kwargs):
            self.vlan_id = Interface.Unit.VlanIdValue()
            self.vlan_id.init_from_list(int_index, lst_src, **kwargs)

        def init_family_from_list(self, int_index, lst_src, **kwargs):
            self.family = Interface.Unit.Family()
            self.family.init_from_list(int_index, lst_src, **kwargs)

        def init_tunnel_from_list(self, int_index, lst_src, **kwargs):
            self.tunnel = Interface.Unit.Tunnel()
            self.tunnel.init_from_list(int_index, lst_src, **kwargs)

        def init_clear_dont_fragment_bit_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Interface.InterfaceInitException

            if lst_src[0][0] != "set":
                raise Interface.InterfaceInitException

            self.clear_dont_fragment_bit = True

        def merge(self, object_other, lst_ignore=None, dict_merge_options=None):
            if dict_merge_options is None:
                dict_merge_options = {}

            if lst_ignore is None:
                lst_ignore = ["lst_src"]

            dict_merge_options["name"] = self.merge_name
            self.merge_base(object_other, lst_ignore=lst_ignore, dict_merge_options=dict_merge_options)

        def merge_name(self, obj_other):
            if self.name != obj_other.name:
                raise Exception

        class VlanIdValue(ConfigurationElement):
            def __init__(self):
                super().__init__()
                self.int_value = None
                self.bool_active = True

            @ConfigurationElement.preprocess_object_init
            def init_from_list(self, int_index, lst_src, **kwargs):
                if len(lst_src) != 1:
                    raise Exception

                self.int_value = int(lst_src[0][int_index])

        class Tunnel(ConfigurationElement):
            def __init__(self):
                super().__init__()
                self.source = None
                self.destination = None
                self.allow_fragmentation = False
                self.parser = Parser()

            def init_from_list(self, int_index, lst_src, **kwargs):
                dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src, {
                        "source": self.init_source_from_list,
                        "destination": self.init_destination_from_list,
                        "allow-fragmentation": self.init_allow_fragmentation_from_list,
                        "key": self.init_allow_fragmentation_from_list,
                        "path-mtu-discovery": self.init_allow_fragmentation_from_list,
                    },
                    **kwargs)

                if dict_ret:
                    pdb.set_trace()

            def init_source_from_list(self, int_index, lst_src, **kwargs):
                if len(lst_src) != 1:
                    pdb.set_trace()
                self.source = lst_src[0][int_index]

            def init_destination_from_list(self, int_index, lst_src, **kwargs):
                if len(lst_src) != 1:
                    pdb.set_trace()
                self.destination = lst_src[0][int_index]

            def init_allow_fragmentation_from_list(self, int_index, lst_src, **kwargs):
                self.allow_fragmentation = True

        class Family(ConfigurationElement):
            def __init__(self):
                super().__init__()
                self.parser = Parser()
                self.protocol = None
                self.dict_vars_vals = OrderedDict()

            def init_from_list(self, int_index, lst_src, **kwargs):
                dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src, {
                        "inet": self.init_inet_from_list,
                        "inet6": self.init_inet6_from_list,
                        "bridge": self.init_bridge_from_list,
                        "ethernet-switching": self.init_ethernet_switching_from_list,
                    },
                    **kwargs)

                if dict_ret:
                    for x in dict_ret:
                        print("####" + x)
                    pdb.set_trace()

            def init_inet6_from_list(self, int_index, lst_src, **kwargs):
                self.protocol = self.__class__.Inet()
                self.protocol.init_from_list(int_index, lst_src, **kwargs)

            def init_inet_from_list(self, int_index, lst_src, **kwargs):
                self.protocol = self.__class__.Inet6()
                self.protocol.init_from_list(int_index, lst_src, **kwargs)

            def init_bridge_from_list(self, int_index, lst_src, **kwargs):
                self.protocol = self.__class__.Bridge()
                self.protocol.init_from_list(int_index, lst_src, **kwargs)

            def init_ethernet_switching_from_list(self, int_index, lst_src, **kwargs):
                self.protocol = self.__class__.EthernetSwitching()
                self.protocol.init_from_list(int_index, lst_src, **kwargs)

            class Inet:
                def __init__(self):
                    self.mtu = None
                    self.addresses = []
                    self.parser = Parser()
                    self.dict_vars_vals = OrderedDict()

                @ConfigurationElement.preprocess_object_init
                def init_from_list(self, int_index, lst_src, **kwargs):
                    # for
                    dict_ret = self.parser.init_objects_from_list(
                        int_index, lst_src, {
                            "mtu": self.init_mtu_from_list,
                            "address": self.init_address_from_list,
                            "filter": ConfigurationElement.init_default_from_list(self),
                            "sampling": ConfigurationElement.init_default_from_list(self),
                        },
                        **kwargs)

                    if dict_ret:
                        pdb.set_trace()

                def init_mtu_from_list(self, int_index, lst_src, **kwargs):
                    if len(lst_src) != 1:
                        pdb.set_trace()

                    if not lst_src[0][int_index].isdigit():
                        raise Exception

                    self.mtu = lst_src[0][int_index]

                def init_address_from_list(self, int_index, lst_src, **kwargs):

                    dict_ret = self.parser.split_list_to_dict(int_index, lst_src)
                    for str_key, lst_lines in dict_ret.items():
                        address = self.Address()
                        address.init_from_list(int_index, lst_lines, **kwargs)
                        self.addresses.append(address)

                class Address:
                    def __init__(self):
                        self.ip_address = None
                        self.parser = Parser()

                    @ConfigurationElement.preprocess_object_init
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        if len(lst_src) < 1:
                            raise Exception

                        self.value = self.__class__.Address_Value()
                        self.value.init_from_list(int_index + 1, lst_src, **kwargs)

                    class Address_Value:
                        def __init__(self):
                            self.value = None
                            self.parser = Parser()

                        @ConfigurationElement.preprocess_object_init
                        def init_from_list(self, int_index, lst_src, **kwargs):
                            self.value = IP()
                            self.value.init_address(lst_src[0][int_index - 1])
                            # pdb.set_trace()
                            dict_ret = self.parser.init_objects_from_list(
                                int_index, lst_src,
                                {
                                    "primary": ConfigurationElement.init_default_bool_from_list(self),
                                    "preferred": ConfigurationElement.init_default_bool_from_list(self),
                                    "vrrp-inet6-group": ConfigurationElement.init_default_from_list(self),
                                },
                                **kwargs)

                            if dict_ret:
                                pdb.set_trace()
                                raise Exception

            class Inet6:
                def __init__(self):
                    self.mtu = None
                    self.addresses = []
                    self.parser = Parser()
                    self.dict_vars_vals = OrderedDict()

                @ConfigurationElement.preprocess_object_init
                def init_from_list(self, int_index, lst_src, **kwargs):
                    dict_ret = self.parser.init_objects_from_list(
                        int_index, lst_src, {
                            "mtu": self.init_mtu_from_list,
                            "address": self.init_address_from_list,
                            "filter": ConfigurationElement.init_default_from_list(self),
                            "sampling": ConfigurationElement.init_default_from_list(self),
                            "dhcp": ConfigurationElement.init_default_from_list(self),
                            "tcp-mss": ConfigurationElement.init_default_from_list(self),
                            "policer": ConfigurationElement.init_default_from_list(self),
                        },
                        **kwargs)

                    if dict_ret:
                        for x in dict_ret:
                            print("###" + x)
                        pdb.set_trace()

                def init_mtu_from_list(self, int_index, lst_src, **kwargs):
                    if len(lst_src) != 1:
                        pdb.set_trace()

                    if not lst_src[0][int_index].isdigit():
                        raise Exception

                    self.mtu = lst_src[0][int_index]

                def init_address_from_list(self, int_index, lst_src, **kwargs):
                    # dict_ret = self.parser.init_objects_from_list(
                    # int_index, lst_src, {},
                    # **kwargs)
                    dict_ret = self.parser.split_list_to_dict(int_index, lst_src)

                    for str_key, lst_lines in dict_ret.items():
                        address = self.Address()
                        address.init_from_list(int_index, lst_lines, **kwargs)
                        self.addresses.append(address)

                class Address:
                    def __init__(self):
                        self.value = None
                        self.parser = Parser()

                    @ConfigurationElement.preprocess_object_init
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        if len(lst_src) < 1:
                            raise Exception

                        self.value = self.__class__.Address_Value()
                        self.value.init_from_list(int_index + 1, lst_src, **kwargs)

                    class Address_Value:
                        def __init__(self):
                            self.value = None
                            self.parser = Parser()

                        @ConfigurationElement.preprocess_object_init
                        def init_from_list(self, int_index, lst_src, **kwargs):
                            self.value = IP()
                            self.value.init_address(lst_src[0][int_index - 1])
                            # pdb.set_trace()
                            dict_ret = self.parser.init_objects_from_list(
                                int_index, lst_src,
                                {
                                    "primary": ConfigurationElement.init_default_bool_from_list(self),
                                    "preferred": ConfigurationElement.init_default_bool_from_list(self),
                                    "vrrp-group": ConfigurationElement.init_default_from_list(self),
                                    "arp": ConfigurationElement.init_default_from_list(self),
                                },
                                **kwargs)

                            if dict_ret:
                                for x in dict_ret:
                                    print("###" + x)
                                pdb.set_trace()
                                raise Exception

            class Bridge:
                def __init__(self):
                    self.parser = Parser()

                @ConfigurationElement.preprocess_object_init
                def init_from_list(self, int_index, lst_src, **kwargs):
                    dict_ret = self.parser.init_objects_from_list(
                        int_index, lst_src, {
                            "interface-mode": ConfigurationElement.init_default_from_list(self),
                            "vlan-id-list": ConfigurationElement.init_default_from_list(self),
                        },
                        **kwargs)

                    if dict_ret:
                        pdb.set_trace()

            class EthernetSwitching(ConfigurationElement):
                def __init__(self):
                    super().__init__()
                    self.parser = Parser()

                @ConfigurationElement.preprocess_object_init
                def init_from_list(self, int_index, lst_src, **kwargs):
                    self.lst_src = lst_src
                    dict_ret = self.parser.init_objects_from_list(
                        int_index, lst_src, {
                            "vlan": ConfigurationElement.init_default_from_list(self),
                            "filter": ConfigurationElement.init_default_from_list(self),
                            "interface-mode": ConfigurationElement.init_default_from_list(self),
                            "port-mode": self.init_port_mode_form_list,
                            "storm-control": ConfigurationElement.init_default_from_list(self),
                        },
                        **kwargs)

                    if dict_ret:
                        for x in dict_ret:
                            print("###" + x)
                        pdb.set_trace()

                def init_port_mode_form_list(self, int_index, lst_src, **kwargs):
                    self.port_mode = self.__class__.PortMode()
                    self.port_mode.init_from_list(int_index, lst_src, **kwargs)

                class PortMode(ConfigurationElement):
                    def __init__(self):
                        super().__init__()
                        self.access = None
                        self.trunk = None
                        self.parser = Parser()

                    @ConfigurationElement.preprocess_object_init
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        dict_ret = self.parser.init_objects_from_list(
                            int_index, lst_src, {
                                "access": self.init_access_form_list,
                                "trunk": self.init_trunk_form_list,
                            },
                            **kwargs)

                        if dict_ret:
                            for x in dict_ret:
                                print("###" + x)
                            pdb.set_trace()

                    def init_access_form_list(self, int_index, lst_src, **kwargs):
                        self.access = self.__class__.Access()
                        self.access.init_from_list(int_index, lst_src, **kwargs)

                    def init_trunk_form_list(self, int_index, lst_src, **kwargs):
                        self.trunk = self.__class__.Trunk()
                        self.trunk.init_from_list(int_index, lst_src, **kwargs)

                    def merge(self, object_other, lst_ignore=None, dict_merge_options=None):
                        if dict_merge_options is None:
                            dict_merge_options = {}

                        if lst_ignore is None:
                            lst_ignore = ["lst_src"]

                        dict_merge_options["access"] = self.merge_access
                        dict_merge_options["trunk"] = self.merge_trunk
                        self.merge_base(object_other, lst_ignore=lst_ignore, dict_merge_options=dict_merge_options)

                    def merge_access(self, obj_other):
                        self.access.merge(obj_other.access)

                    def merge_trunk(self, obj_other):
                        self.access.merge(obj_other.access)

                    class Access(ConfigurationElement):
                        def __init__(self):
                            super().__init__()
                            self.parser = Parser()
                            self.value = None

                        @ConfigurationElement.preprocess_object_init
                        def init_from_list(self, int_index, lst_src, **kwargs):
                            dict_ret = self.parser.init_objects_from_list(
                                int_index, lst_src, {
                                    "access": self.init_access_form_list,
                                    "trunk": self.init_trunk_form_list,
                                },
                                **kwargs)

                            if dict_ret:
                                for x in dict_ret:
                                    print("###" + x)
                                pdb.set_trace()

                        def init_access_form_list(self, int_index, lst_src, **kwargs):
                            pdb.set_trace()

                        def init_trunk_form_list(self, int_index, lst_src, **kwargs):
                            pdb.set_trace()

                    class Trunk(ConfigurationElement):
                        def __init__(self):
                            super().__init__()
                            self.parser = Parser()
                            self.value = None

                        @ConfigurationElement.preprocess_object_init
                        def init_from_list(self, int_index, lst_src, **kwargs):
                            dict_ret = self.parser.init_objects_from_list(
                                int_index, lst_src, {
                                    "access": self.init_access_form_list,
                                    "trunk": self.init_trunk_form_list,
                                },
                                **kwargs)

                            if dict_ret:
                                for x in dict_ret:
                                    print("###" + x)
                                pdb.set_trace()

                        def init_access_form_list(self, int_index, lst_src, **kwargs):
                            pdb.set_trace()

                        def init_trunk_form_list(self, int_index, lst_src, **kwargs):
                            pdb.set_trace()

    class InterfaceInitException(Exception):
        pass

    class InterfaceInitUnhandledDeactivateException(Exception):
        pass


class InterfaceLo(Interface):
    def __init__(self):
        super().__init__()


class InterfaceFXP(Interface):
    def __init__(self):
        super().__init__()


class InterfaceGE(Interface):
    def __init__(self):
        super().__init__()


class InterfaceGR(Interface):
    def __init__(self):
        super().__init__()


class InterfaceXE(Interface):
    def __init__(self):
        super().__init__()


class InterfaceAE(Interface):
    def __init__(self):
        super().__init__()


class InterfaceET(Interface):
    def __init__(self):
        super().__init__()


class InterfaceST(Interface):
    def __init__(self):
        super().__init__()


class InterfaceVlan(Interface):
    def __init__(self):
        super().__init__()


class InterfaceReth(Interface):
    def __init__(self):
        super().__init__()


class InterfaceFab(Interface):
    def __init__(self):
        super().__init__()


class InterfaceVME(Interface):
    def __init__(self):
        super().__init__()


class InterfaceME(Interface):
    def __init__(self):
        super().__init__()


class InterfaceEM(Interface):
    def __init__(self):
        super().__init__()


class InterfaceLT(Interface):
    def __init__(self):
        super().__init__()


class InterfaceIRB(Interface):
    def __init__(self):
        super().__init__()


class InterfaceInterRange(Interface):
    def __init__(self):
        super().__init__()
        self.ranges = []

    def init_from_list(self, int_index, lst_src, **kwargs):
        dict_src = self.parser.split_list_to_dict(int_index, lst_src)
        for str_name, lst_lines in dict_src.items():
            rng = self.__class__.Range(str_name)
            rng.init_from_list(int_index + 1, lst_lines, **kwargs)
            self.ranges.append(rng)

    class Range(ConfigurationElement):
        def __init__(self, str_name):
            super().__init__()
            self.name = str_name
            self.parser = Parser()
            self.lst_str_members = []
            self.lst_members = []
            self.lst_inited_members = []

        def init_from_list(self, int_index, lst_src, **kwargs):
            self.lst_src = lst_src
            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src,
                {
                    "member": self.init_member_from_list,
                    "member-range": self.init_member_range_from_list,
                    "unit": self.init_unit_from_list,
                },
                **kwargs
            )

            if dict_ret:
                for x in dict_ret:
                    print("####" + x)
                pdb.set_trace()

        def init_member_from_list(self, int_index, lst_src, **kwargs):
            for lst_line in lst_src:
                if lst_line[0] != "set":
                    raise Exception

                lst_inter_names = self.__class__.parse_range_string(lst_line[int_index].strip('"'))
                self.init_members_from_names(int_index, lst_inter_names, **kwargs)

        def init_member_range_from_list(self, int_index, lst_src, **kwargs):
            for lst_line in lst_src:
                if lst_line[0] != "set":
                    raise Exception

                lst_inter_names = self.__class__.parse_range_list(lst_line[int_index:])
                self.init_members_from_names(int_index, lst_inter_names, **kwargs)

        def init_members_from_names(self, int_index, lst_inter_names, **kwargs):
            for str_inter_name in lst_inter_names:
                lst_found = self.parser.get_objects_by_values({"name": str_inter_name}, self.lst_str_members,
                                                              int_limit=1)
                if lst_found:
                    raise Exception

                lst_found = self.parser.get_objects_by_values({"name": str_inter_name}, kwargs["lst_interfaces"],
                                                              int_limit=1)
                if lst_found:
                    self.lst_inited_members += lst_found
                    continue

                self.lst_str_members.append(str_inter_name)
                cls = JuniperBaseDevice.get_interface_class_by_interface_name(str_inter_name)
                if not cls:
                    raise Exception
                inter_member = cls()
                inter_member.name = str_inter_name
                self.lst_members.append(inter_member)

        @staticmethod
        def parse_range_string(str_src):
            lst_ret = []
            if "[" in str_src:
                if str_src.count("[") != 1:
                    raise Exception

                if str_src.count("]") != 1:
                    raise Exception

                str_prefix = str_src[:str_src.find("[")]
                str_range = str_src[str_src.find("[") + 1: str_src.find("]")]
                if "-" in str_range:
                    str_start, str_end = str_range.split("-")
                    lst_ret = list(map(lambda x:
                                       str_prefix + str(x), range(int(str_start), int(str_end) + 1)))
                else:
                    raise Exception
            else:
                result_search = re.search('^[\D]+-[\d]+/[\d]+/[\d]+$', str_src)
                if result_search.group(0) != str_src:
                    raise Exception
                lst_ret = [str_src]
            return lst_ret

        @staticmethod
        def parse_range_list(lst_src):
            lst_ret = []
            if len(lst_src) == 3:
                if lst_src[1] != "to":
                    raise Exception

                str_prefix_start, str_suffix_start = lst_src[0].split("-")
                str_prefix_end, str_suffix_end = lst_src[2].split("-")
                if str_prefix_start != str_prefix_end:
                    raise Exception

                lst_inter_triple_start = str_suffix_start.split("/")
                lst_inter_triple_end = str_suffix_end.split("/")

                if lst_inter_triple_start[0] != lst_inter_triple_end[0]:
                    raise Exception

                if lst_inter_triple_start[1] != lst_inter_triple_end[1]:
                    raise Exception

                lst_ret = list(map(lambda x: "%s-%s/%s/%s" %
                                             (str_prefix_start, lst_inter_triple_start[0], lst_inter_triple_start[1], x)
                                   , range(int(lst_inter_triple_start[2]), int(lst_inter_triple_end[2]) + 1)))
            else:
                raise Exception

            return lst_ret

        def init_unit_from_list(self, int_index, lst_src, **kwargs):
            for interface in self.lst_members:
                interface.init_from_list(int_index - 1, lst_src, **kwargs)

            for interface in self.lst_inited_members:
                inter_new = interface.__class__()
                inter_new.init_from_list(int_index - 1, lst_src, **kwargs)
                inter_new.name = interface.name
                interface.merge(inter_new)
                self.lst_members.append(interface)


class JuniperBaseDevice(object):
    def __init__(self):
        self.parser = Parser()
        self.interfaces = []
        self.groups = []
        self.dict_func_inits = {
            "version": self.init_version_from_list,
            "interfaces": self.init_interfaces_from_list,
            "configuration": self.init_configuration_from_list,
            "groups": self.init_groups_from_list,
            "apply-groups": ConfigurationElement.init_default_from_list(self),
            "system": ConfigurationElement.init_default_from_list(self),
            "chassis": ConfigurationElement.init_default_from_list(self),
            "services": ConfigurationElement.init_default_from_list(self),
            "snmp": ConfigurationElement.init_default_from_list(self),
            "forwarding-options": ConfigurationElement.init_default_from_list(self),
            "event-options": ConfigurationElement.init_default_from_list(self),
            "routing-options": ConfigurationElement.init_default_from_list(self),
            "protocols": ConfigurationElement.init_default_from_list(self),
            "policy-options": ConfigurationElement.init_default_from_list(self),
            "firewall": ConfigurationElement.init_default_from_list(self),
            "routing-instances": ConfigurationElement.init_default_from_list(self),
            "bridge-domains": ConfigurationElement.init_default_from_list(self),
            "switch-options": ConfigurationElement.init_default_from_list(self),
            "vlans": ConfigurationElement.init_default_from_list(self),
            "security": ConfigurationElement.init_default_from_list(self),
            "access": ConfigurationElement.init_default_from_list(self),
            "virtual-chassis": ConfigurationElement.init_default_from_list(self),
            "ethernet-switching-options": ConfigurationElement.init_default_from_list(self),
            "class-of-service": ConfigurationElement.init_default_from_list(self),
            "poe": ConfigurationElement.init_default_from_list(self),
            "applications": ConfigurationElement.init_default_from_list(self),
            "accounting-options": ConfigurationElement.init_default_from_list(self),
            "logical-systems": ConfigurationElement.init_default_from_list(self),
        }

    # def init_deactivated_object(self,
    # @init_deactivated_object
    def init_from_list(self, lst_src, int_index=1):
        self.lst_src = lst_src

        def func_key(str_src):
            if str_src == "groups":
                return 0
            return 1

        dict_ret = self.parser.init_objects_from_list(int_index, lst_src, self.dict_func_inits, func_key=func_key)
        if dict_ret:
            pdb.set_trace()

    def init_groups_from_list(self, int_index, lst_src, **kwargs):
        dict_src = self.parser.split_list_to_dict(int_index, lst_src)
        for str_name, lst_lines in dict_src.items():
            grp = self.__class__.Group()
            grp.init_from_list(int_index + 1, lst_lines)
            self.groups.append(grp)

    def init_configuration_from_list(self, int_index, lst_src, **kwargs):
        pdb.set_trace()

    def init_version_from_list(self, int_index, lst_src, **kwargs):
        if len(lst_src) != 1:
            raise Exception

        lst_src = lst_src[0]
        self.version = lst_src[2]

    def init_interfaces_from_list(self, int_index, lst_src, **kwargs):
        dict_src = self.parser.split_list_to_dict(int_index, lst_src)

        def func_key(str_src):
            if str_src.startswith("ae"):
                return 0
            if str_src.startswith("interface-range"):
                return 10
            return 1

        lst_ordered_src = sorted(list(dict_src.keys()), key=func_key)

        for str_name in lst_ordered_src:
            lst_lines = dict_src[str_name]
            self.init_and_append_interface(str_name, int_index + 1, lst_lines)

    def init_and_append_interface(self, str_name, int_index, lst_lines):
        for type_interface in JuniperBaseDevice.InterfaceType:
            if str_name.startswith(type_interface.name.lower()):
                cls_inter = type_interface.value
                break

            if str_name.replace("-", "_").startswith(type_interface.name.lower()):
                cls_inter = type_interface.value
                break
        else:
            print(str_name)
            pdb.set_trace()
            raise Exception(str_name)

        interface = cls_inter()
        interface.init_from_list(int_index, lst_lines, lst_interfaces=self.interfaces, lst_groups=self.groups)
        self.interfaces.append(interface)

    def init_snmp_from_list(self, lst_src):
        pdb.set_trace()

    def init_forwarding_options_from_list(self, lst_src):
        pdb.set_trace()

    def init_event_options_from_list(self, lst_src):
        pdb.set_trace()

    def init_routing_options_from_list(self, lst_src):
        pdb.set_trace()

    def init_protocols_from_list(self, int_index, lst_src, **kwargs):
        self.protocols = self.__class__.Protocols()
        self.protocols.init_from_list(int_index, lst_src, **kwargs)

    def init_bgp_from_list(self, int_index, lst_src, **kwargs):
        pdb.set_trace()

    class Group(ConfigurationElement):
        def __init__(self):
            super().__init__()
            self.name = None
            self.parser = Parser()

        @ConfigurationElement.preprocess_object_init
        def init_from_list(self, int_index, lst_src, **kwargs):
            self.name = lst_src[0][int_index - 1]
            self.lst_src = lst_src

    class Protocols(ConfigurationElement):
        def __init__(self):
            super().__init__()
            self.parser = Parser()

        def init_from_list(self, int_index, lst_src, **kwargs):
            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src,
                {
                    "bgp": self.init_bgp_from_list,
                    "layer2-control": ConfigurationElement.init_default_from_list(self),
                    "lldp": ConfigurationElement.init_default_from_list(self),
                    "vrrp": ConfigurationElement.init_default_from_list(self),
                    "ospf": ConfigurationElement.init_default_from_list(self),
                    "lldp-med": ConfigurationElement.init_default_from_list(self),
                    "igmp-snooping": ConfigurationElement.init_default_from_list(self),
                    "rstp": ConfigurationElement.init_default_from_list(self),
                    "l2-learning": ConfigurationElement.init_default_from_list(self),
                    "dcbx": ConfigurationElement.init_default_from_list(self),
                    "igmp": ConfigurationElement.init_default_from_list(self),
                    "mld": ConfigurationElement.init_default_from_list(self),
                    "bfd": ConfigurationElement.init_default_from_list(self),
                    "sflow": ConfigurationElement.init_default_from_list(self),
                    "stp": ConfigurationElement.init_default_from_list(self),
                    "oam": ConfigurationElement.init_default_from_list(self),
                },
                **kwargs
            )

            if dict_ret:
                for x in dict_ret:
                    print("####" + x)
                pdb.set_trace()

        def init_bgp_from_list(self, int_index, lst_src, **kwargs):
            self.bgp = self.__class__.Bgp()
            self.bgp.init_from_list(int_index, lst_src, **kwargs)
            return

        class Bgp(ConfigurationElement):
            def __init__(self):
                super().__init__()
                self.parser = Parser()
                self.groups = []

            def init_from_list(self, int_index, lst_src, **kwargs):
                dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src,
                    {
                        "traceoptions": ConfigurationElement.init_default_from_list(self),
                        "group": self.init_group_from_list,
                        "precision-timers": self.init_group_from_list,
                    },
                    **kwargs
                )

                if dict_ret:
                    pdb.set_trace()

            def init_group_from_list(self, int_index, lst_src, **kwargs):
                dict_src = self.parser.split_list_to_dict(int_index, lst_src)
                for str_name, lst_lines in dict_src.items():
                    grp = self.__class__.Group(str_name)
                    grp.init_from_list(int_index + 1, lst_lines, **kwargs)
                    self.groups.append(grp)

            class Group:
                def __init__(self, str_name):
                    self.name = str_name
                    self.parser = Parser()
                    self.bool_active = True
                    self.neighbors = []

                @ConfigurationElement.preprocess_object_init
                def init_from_list(self, int_index, lst_src, **kwargs):
                    dict_ret = self.parser.init_objects_from_list(
                        int_index, lst_src,
                        {
                            'type': ConfigurationElement.init_default_from_list(self),
                            'import': ConfigurationElement.init_default_from_list(self),
                            'export': ConfigurationElement.init_default_from_list(self),
                            'remove-private': ConfigurationElement.init_default_bool_from_list(self),
                            'peer-as': ConfigurationElement.init_default_from_list(self),
                            'multipath': ConfigurationElement.init_default_from_list(self),
                            'multihop': ConfigurationElement.init_default_from_list(self),
                            'neighbor': self.init_neighbor_from_list,
                            'traceoptions': ConfigurationElement.init_default_from_list(self),
                            'cluster': ConfigurationElement.init_default_from_list(self),
                            'family': ConfigurationElement.init_default_from_list(self),
                            'ttl': ConfigurationElement.init_default_from_list(self),
                            'keep': ConfigurationElement.init_default_from_list(self),
                            'accept-remote-nexthop': ConfigurationElement.init_default_bool_from_list(self),
                            'hold-time': ConfigurationElement.init_default_from_list(self),
                            'authentication-key': ConfigurationElement.init_default_from_list(self),
                            'local-as': ConfigurationElement.init_default_from_list(self),
                            'bfd-liveness-detection': ConfigurationElement.init_default_from_list(self),
                            'description': ConfigurationElement.init_default_from_list(self),
                            'local-address': ConfigurationElement.init_default_from_list(self),
                            'graceful-restart': ConfigurationElement.init_default_from_list(self),
                            'advertise-peer-as': ConfigurationElement.init_default_from_list(self),
                            'advertise-inactive': ConfigurationElement.init_default_from_list(self),
                        },
                        **kwargs
                    )

                    if dict_ret:
                        for x in dict_ret:
                            print("####" + x)
                        pdb.set_trace()

                def init_neighbor_from_list(self, int_index, lst_src, **kwargs):
                    dict_src = self.parser.split_list_to_dict(int_index, lst_src)
                    for str_key, lst_lines in dict_src.items():
                        nbr = self.__class__.Neighbor(str_key)
                        nbr.init_from_list(int_index + 1, lst_lines, **kwargs)
                        self.neighbors.append(nbr)

                class Neighbor:
                    def __init__(self, str_name):
                        self.name = str_name
                        self.value = IP()
                        self.value.init_host(str_name)
                        self.parser = Parser()
                        self.bool_active = True

                    @ConfigurationElement.preprocess_object_init
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        dict_ret = self.parser.init_objects_from_list(
                            int_index, lst_src,
                            {
                                'family': ConfigurationElement.init_default_from_list(self),
                                'authentication-key': ConfigurationElement.init_default_from_list(self),
                                'description': ConfigurationElement.init_default_from_list(self),
                                'keep': ConfigurationElement.init_default_from_list(self),
                                'hold-time': ConfigurationElement.init_default_from_list(self),
                                'multipath': ConfigurationElement.init_default_from_list(self),
                                'mtu-discovery': ConfigurationElement.init_default_from_list(self),
                                'local-address': ConfigurationElement.init_default_from_list(self),
                                'bfd-liveness-detection': ConfigurationElement.init_default_from_list(self),
                                'import': ConfigurationElement.init_default_from_list(self),
                                'export': ConfigurationElement.init_default_from_list(self),
                                'peer-as': ConfigurationElement.init_default_from_list(self),
                                'traceoptions': ConfigurationElement.init_default_from_list(self),
                                'remove-private': ConfigurationElement.init_default_from_list(self),
                                'as-override': ConfigurationElement.init_default_from_list(self),
                                'multihop': ConfigurationElement.init_default_from_list(self),
                            },
                            **kwargs
                        )

                        if dict_ret:
                            for x in dict_ret:
                                print("####" + x)
                            pdb.set_trace()

    @staticmethod
    def get_interface_class_by_interface_name(str_src):
        for type_interface in JuniperBaseDevice.InterfaceType:
            if str_src.startswith(type_interface.name.lower()):
                cls_inter = type_interface.value
                break

            if str_src.replace("-", "_").startswith(type_interface.name.lower()):
                cls_inter = type_interface.value
                break
        else:
            raise Exception(str_src)

        return cls_inter

    class InterfaceType(Enum):
        LO = InterfaceLo
        FXP = InterfaceFXP
        GE = InterfaceGE
        XE = InterfaceXE
        GR = InterfaceGR
        AE = InterfaceAE
        ME = InterfaceME
        EM = InterfaceEM
        LT = InterfaceLT
        IRB = InterfaceIRB
        ET = InterfaceET
        ST = InterfaceST
        VLAN = InterfaceVlan
        RETH = InterfaceReth
        FAB = InterfaceFab
        VME = InterfaceVME
        INTERFACE_RANGE = InterfaceInterRange
