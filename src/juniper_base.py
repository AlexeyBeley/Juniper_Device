import pdb
from collections import OrderedDict
from enum import Enum

from src.ip import IP
from src.parser import Parser


class ConfigurationElement:
    def __init__(self):
        self.value = None
        self.bool_active = True
        self.lst_src = None

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

        @ConfigurationElement.preprocess_deactivated_object
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
    def init_default_bool_from_list(obj_caller):
        """obj_caller is the one which has subclasses in it"""

        def generate_init_bool_element(int_index, lst_src, obj_caller=obj_caller, **kwargs):
            obj_ret = ConfigurationElement.init_configuration_element_default_from_list(int_index, lst_src,
                                                                                        obj_caller=obj_caller, **kwargs)
            setattr(obj_caller, obj_ret.__class__.get_attr_name(), obj_ret)
            obj_ret.value = True

        return generate_init_bool_element

    def init_from_list(self, int_index, lst_src, **kwargs):
        raise NotImplementedError("todo:")

    @staticmethod
    def preprocess_deactivated_object(func_src):
        def func_ret(self, int_index, lst_src, **kwargs):
            for i in range(len(lst_src)):
                lst_line = lst_src[i]

                if lst_line[0] != "set":
                    if lst_line[0] != "deactivate":
                        pdb.set_trace()
                        raise Exception

                    if len(lst_line) == int_index:
                        self.bool_active = False
                        if len(lst_src) - 1 != i:
                            pdb.set_trace()
                            raise Exception
                        lst_src = lst_src[:-1]

            func_src(self, int_index, lst_src, **kwargs)

        return func_ret

    @classmethod
    def get_attr_name(cls):
        str_ret = cls.__name__[0].lower()
        for i in range(1, len(cls.__name__)):
            str_current_char = cls.__name__[i]
            if str_current_char.istitle():
                pdb.set_trace()
                str_ret += "_" + str_current_char.lower()
            else:
                str_ret += str_current_char.lower()

        return str_ret


class Interface(object):
    def __init__(self, name):
        self.name = name
        self.parser = Parser()
        self.units = []
        self.bool_active = True
        self.bool_enabled = True
        self.lst_src = None

    @ConfigurationElement.preprocess_deactivated_object
    def init_from_list(self, int_index, lst_src, **kwargs):
        self.lst_src = lst_src
        dict_init_options = self.get_dict_init_options()
        dict_ret = self.parser.init_objects_from_list(
            int_index, lst_src, dict_init_options, **kwargs)

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
            "gigether-options": self.init_gigether_options_from_list,
            "no-gratuitous-arp-reply": ConfigurationElement.init_default_bool_from_list(self),
            "no-gratuitous-arp-request": ConfigurationElement.init_default_bool_from_list(self),
            "aggregated-ether-options": self.init_aggregated_ether_options_from_list,
            "disable": self.init_disable_from_list,
            "speed": ConfigurationElement.init_default_from_list(self),
            "link-mode": ConfigurationElement.init_default_from_list(self),
        }
        return dict_ret

    def init_disable_from_list(self, int_index, lst_src, **kwargs):
        if len(lst_src) != 1:
            raise Exception

        if lst_src[0][0] != "set":
            raise Exception

        self.bool_enabled = False

    def init_aggregated_ether_options_from_list(self, int_index, lst_src, **kwargs):
        self.aggregated_ether_options = Interface.AggregatedEtherOptions()
        self.aggregated_ether_options.init_from_list(int_index, lst_src, **kwargs)

    def init_description_from_list(self, int_index, lst_src, **kwargs):
        self.description = Interface.DescriptionValue()
        self.description.init_from_list(int_index, lst_src, **kwargs)

    def init_gigether_options_from_list(self, int_index, lst_src, **kwargs):
        self.gigether_options = Interface.GigetherOptions()
        self.gigether_options.init_from_list(int_index, lst_src, **kwargs)

    def init_unit_from_list(self, int_index, lst_src, **kwargs):
        # dict_ret = self.parser.init_objects_from_list(int_index, lst_src, {}, **kwargs)
        dict_ret = self.parser.split_list_to_dict(int_index, lst_src)
        for str_unit_name, lst_lines in dict_ret.items():
            unit = Interface.Unit(str_unit_name)
            unit.init_from_list(int_index + 1, lst_lines, **kwargs)
            self.units.append(unit)

    def merge(self, inter_other):
        dict_merge_options = {
            "units": self.merge_units
        }

        self.parser.merge_objects(self, inter_other, inter_other.__class__(self.name), dict_merge_options)

    def merge_units(self, inter_other):
        for unit_other in inter_other.units:
            lst_self_units =  self.parser.get_objects_by_values({"name": unit_other.name}, self.units, int_limit=1)
            if not lst_self_units:
                self.units.append(unit_other)
            else:
                lst_self_units[0].merge(unit_other)

    class NoGratuitousArpReply_:
        def __init__(self):
            self.bool_value = None
            self.bool_active = False

        @ConfigurationElement.preprocess_deactivated_object
        def init_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception

            self.bool_value = True

        @staticmethod
        def get_attr_name():
            return "no_gratuitous_arp_reply"

    class NoGratuitousArpRequest:
        def __init__(self):
            self.bool_value = None
            self.bool_active = False

        @ConfigurationElement.preprocess_deactivated_object
        def init_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception

            self.bool_value = True

        @staticmethod
        def get_attr_name():
            return "no_gratuitous_arp_request"

    class AggregatedEtherOptions:
        def __init__(self):
            self.lacp = None
            self.bool_active = False
            self.parser = Parser()

        @ConfigurationElement.preprocess_deactivated_object
        def init_from_list(self, int_index, lst_src, **kwargs):
            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src,
                {"lacp": ConfigurationElement.init_default_from_list(self)
                 },
                **kwargs)

            if dict_ret:
                pdb.set_trace()

        def init_lacp_from_list(self, int_index, lst_src, **kwargs):
            pdb.set_trace()
            self.aggregated_ether_options = Interface.AggregatedEtherOptions()
            self.aggregated_ether_options.init_from_list(int_index, lst_src, **kwargs)

        class Lacp(ConfigurationElement):
            def __init__(self):
                self.lacp = None
                self.bool_active = False
                self.parser = Parser()

            @ConfigurationElement.preprocess_deactivated_object
            def init_from_list(self, int_index, lst_src, **kwargs):
                dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src,
                    {
                        "active": ConfigurationElement.init_default_bool_from_list(self),
                        "periodic": ConfigurationElement.init_default_from_list(self),
                    },
                    **kwargs)

                if dict_ret:
                    pdb.set_trace()

    class DescriptionValue:
        def __init__(self):
            self.str_value = None
            self.bool_active = False

        @ConfigurationElement.preprocess_deactivated_object
        def init_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception
            self.str_value = lst_src[0][int_index]

    class GigetherOptions:
        def __init__(self):
            self.bool_active = True
            self.parser = Parser()

        @ConfigurationElement.preprocess_deactivated_object
        def init_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception

            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src, {
                    "802.3ad": self.init_802_3ad_from_list,
                    "no-auto-negotiation": ConfigurationElement.init_default_bool_from_list(self),
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
                self.parser = Parser()

            @ConfigurationElement.preprocess_deactivated_object
            def init_from_list(self, int_index, lst_src, **kwargs):
                if len(lst_src) != 1:
                    raise Exception

                inter_ret = self.parser.get_objects_by_values({"name": lst_src[0][int_index]}, kwargs["lst_interfaces"],
                                                              int_limit=1)
                if not inter_ret:
                    raise Exception

                self.ae_interface = inter_ret

    class Unit(object):
        def __init__(self, name):
            self.name = name
            self.vlan_id = None
            self.parser = Parser()
            self.dict_vars_vals = {}

        @ConfigurationElement.preprocess_deactivated_object
        def init_from_list(self, int_index, lst_src, **kwargs):
            self.lst_src = lst_src
            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src, {
                    "clear-dont-fragment-bit": self.init_clear_dont_fragment_bit_from_list,
                    "description": self.init_description_from_list,
                    "tunnel": self.init_tunnel_from_list,
                    "family": self.init_family_from_list,
                    "vlan-id": self.init_vlan_id_from_list,
                    "encapsulation": ConfigurationElement.init_default_from_list(self),
                    "peer-unit": ConfigurationElement.init_default_from_list(self),
                },
                **kwargs)
            if dict_ret:
                pdb.set_trace()

        def init_vlan_id_from_list(self, int_index, lst_src, **kwargs):
            self.vlan_id = Interface.Unit.VlanIdValue()
            self.vlan_id.init_from_list(int_index, lst_src, **kwargs)

        def init_default_from_list(self, int_index, lst_src, **kwargs):
            self.dict_vars_vals[lst_src[0][int_index - 1]] = lst_src

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

        def init_description_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Interface.InterfaceInitException

            if lst_src[0][0] != "set":
                raise Interface.InterfaceInitException

            self.description = Interface.DescriptionValue()
            self.description.init_from_list(int_index, lst_src, **kwargs)

        def merge(self, unit_other):
            dict_merge_options = {"family": self.merge_family}
            self.parser.merge_objects(self, unit_other, unit_other.__class__(self.name), dict_merge_options)

        def merge_family(self, unit_other):
            self.family.merge(unit_other.family)

        class VlanIdValue:
            def __init__(self):
                self.int_value = None
                self.bool_active = True

            @ConfigurationElement.preprocess_deactivated_object
            def init_from_list(self, int_index, lst_src, **kwargs):
                if len(lst_src) != 1:
                    raise Exception

                self.int_value = int(lst_src[0][int_index])

        class Tunnel:
            def __init__(self):
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

        class Family:
            def __init__(self):
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

            def merge(self, family_other):
                dict_merge_options = {"protocol": self.merge_protocol}
                self.parser.merge_objects(self, family_other, self.__class__(), dict_merge_options)

            def merge_protocol(self, family_other):
                self.protocol.merge(family_other.protocol)

            class Inet:
                def __init__(self):
                    self.mtu = None
                    self.addresses = []
                    self.parser = Parser()
                    self.dict_vars_vals = OrderedDict()

                @ConfigurationElement.preprocess_deactivated_object
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

                    @ConfigurationElement.preprocess_deactivated_object
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        if len(lst_src) < 1:
                            raise Exception

                        self.value = self.__class__.Address_Value()
                        self.value.init_from_list(int_index + 1, lst_src, **kwargs)

                    class Address_Value:
                        def __init__(self):
                            self.value = None
                            self.parser = Parser()

                        @ConfigurationElement.preprocess_deactivated_object
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

                @ConfigurationElement.preprocess_deactivated_object
                def init_from_list(self, int_index, lst_src, **kwargs):
                    dict_ret = self.parser.init_objects_from_list(
                        int_index, lst_src, {
                            "mtu": self.init_mtu_from_list,
                            "address": self.init_address_from_list,
                            "filter": ConfigurationElement.init_default_from_list(self),
                            "sampling": ConfigurationElement.init_default_from_list(self),
                            "dhcp": ConfigurationElement.init_default_from_list(self),
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

                    @ConfigurationElement.preprocess_deactivated_object
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        if len(lst_src) < 1:
                            raise Exception

                        self.value = self.__class__.Address_Value()
                        self.value.init_from_list(int_index + 1, lst_src, **kwargs)

                    class Address_Value:
                        def __init__(self):
                            self.value = None
                            self.parser = Parser()

                        @ConfigurationElement.preprocess_deactivated_object
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
                                },
                                **kwargs)

                            if dict_ret:
                                pdb.set_trace()
                                raise Exception

            class Bridge:
                def __init__(self):
                    self.parser = Parser()

                @ConfigurationElement.preprocess_deactivated_object
                def init_from_list(self, int_index, lst_src, **kwargs):
                    dict_ret = self.parser.init_objects_from_list(
                        int_index, lst_src, {
                            "interface-mode": ConfigurationElement.init_default_from_list(self),
                            "vlan-id-list": ConfigurationElement.init_default_from_list(self),
                        },
                        **kwargs)

                    if dict_ret:
                        pdb.set_trace()

            class EthernetSwitching:
                def __init__(self):
                    self.parser = Parser()

                @ConfigurationElement.preprocess_deactivated_object
                def init_from_list(self, int_index, lst_src, **kwargs):
                    dict_ret = self.parser.init_objects_from_list(
                        int_index, lst_src, {
                            "vlan": ConfigurationElement.init_default_from_list(self),
                            "filter": ConfigurationElement.init_default_from_list(self),
                            "interface-mode": ConfigurationElement.init_default_from_list(self),
                            "port-mode": ConfigurationElement.init_default_from_list(self),
                        },
                        **kwargs)

                    if dict_ret:
                        for x in dict_ret:
                            print("###" + x)
                        pdb.set_trace()

                def merge(self, protocol_other):
                    dict_merge_options = {"port_mode": self.merge_port_mode}
                    self.parser.merge_objects(self, protocol_other, self.__class__(), dict_merge_options)

                def merge_port_mode(self, object_other):
                    pdb.set_trace()
                    self.port_mode.merge(object_other.protocol)

    class InterfaceInitException(Exception):
        pass

    class InterfaceInitUnhandledDeactivateException(Exception):
        pass


class InterfaceLo(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceFXP(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceGE(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceGR(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceXE(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceAE(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceET(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceST(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceVlan(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceVME(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceME(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceLT(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceIRB(Interface):
    def __init__(self, name):
        super().__init__(name)


class InterfaceInterRange(Interface):
    def __init__(self, name):
        super().__init__(name)
        self.ranges = []

    def init_from_list(self, int_index, lst_src, **kwargs):
        dict_src = self.parser.split_list_to_dict(int_index, lst_src)
        for str_name, lst_lines in dict_src.items():
            rng = self.__class__.Range(str_name)
            rng.init_from_list(int_index + 1, lst_lines, **kwargs)
            self.ranges.append(rng)

    class Range:
        def __init__(self, str_name):
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
                    inter_member = cls(str_inter_name)
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
                raise Exception

            return lst_ret

        def init_unit_from_list(self, int_index, lst_src, **kwargs):
            for interface in self.lst_members:
                interface.init_from_list(int_index - 1, lst_src, **kwargs)

            for interface in self.lst_inited_members:
                inter_new = interface.__class__(interface.name)
                inter_new.init_from_list(int_index - 1, lst_src, **kwargs)
                interface.merge(inter_new)
                self.lst_members.append(interface)

class JuniperBaseDevice(object):
    def __init__(self):
        self.parser = Parser()
        self.interfaces = []

    # def init_deactivated_object(self,
    # @init_deactivated_object
    def init_from_list(self, lst_src, int_index=1):
        self.lst_src = lst_src
        dict_ret = self.parser.init_objects_from_list(
            int_index, lst_src,
            {
                "version": self.init_version_from_list,
                "interfaces": self.init_interfaces_from_list,
                "configuration": self.init_configuration_from_list,
                "groups": ConfigurationElement.init_default_from_list(self),
                "apply-groups": ConfigurationElement.init_default_from_list(self),
                "system": ConfigurationElement.init_default_from_list(self),
                "chassis": ConfigurationElement.init_default_from_list(self),
                "services": ConfigurationElement.init_default_from_list(self),
                "snmp": ConfigurationElement.init_default_from_list(self),
                "forwarding-options": ConfigurationElement.init_default_from_list(self),
                "event-options": ConfigurationElement.init_default_from_list(self),
                "routing-options": ConfigurationElement.init_default_from_list(self),
                "protocols": self.init_protocols_from_list,
                "policy-options": ConfigurationElement.init_default_from_list(self),
                "firewall": ConfigurationElement.init_default_from_list(self),
                "routing-instances": ConfigurationElement.init_default_from_list(self),
                "bridge-domains": ConfigurationElement.init_default_from_list(self),
                "switch-options": ConfigurationElement.init_default_from_list(self),
                "vlans": ConfigurationElement.init_default_from_list(self),
                "security": ConfigurationElement.init_default_from_list(self),
                "access": ConfigurationElement.init_default_from_list(self),
                "virtual-chassis": ConfigurationElement.init_default_from_list(self),
            }
        )

        if dict_ret:
            for x in dict_ret:
                print("####" + x)
            pdb.set_trace()

    def init_configuration_from_list(self, int_index, lst_src, **kwargs):
        pdb.set_trace()

    def init_version_from_list(self, int_index, lst_src, **kwargs):
        if len(lst_src) != 1:
            raise Exception

        lst_src = lst_src[0]
        self.version = lst_src[2]

    def init_groups_from_list(self, lst_src):
        pdb.set_trace()

    def init_apply_groups_from_list(self, lst_src):
        pdb.set_trace()

    def init_system_from_list(self, lst_src):
        pdb.set_trace()

    def init_chassis_from_list(self, lst_src):
        pdb.set_trace()

    def init_services_from_list(self, lst_src):
        pdb.set_trace()

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

        interface = cls_inter(str_name)
        interface.init_from_list(int_index, lst_lines, lst_interfaces=self.interfaces)
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

    def init_policy_options_from_list(self, lst_src):
        pdb.set_trace()

    def init_firewall_from_list(self, lst_src):
        pdb.set_trace()

    def init_routing_instances_from_list(self, lst_src):
        pdb.set_trace()

    class Protocols:
        def __init__(self):
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
                self.parser = Parser()
                self.groups = []

            def init_from_list(self, int_index, lst_src, **kwargs):
                dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src,
                    {
                        "traceoptions": ConfigurationElement.init_default_from_list(self),
                        "group": self.init_group_from_list,
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

                @ConfigurationElement.preprocess_deactivated_object
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
                        nbr.init_from_list(int_index + 1, lst_src, **kwargs)
                        self.neighbors.append(nbr)

                class Neighbor:
                    def __init__(self, str_name):
                        self.name = str_name
                        self.value = IP()
                        self.value.init_host(str_name)
                        self.parser = Parser()
                        self.bool_active = True

                    @ConfigurationElement.preprocess_deactivated_object
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
        LT = InterfaceLT
        IRB = InterfaceIRB
        ET = InterfaceET
        ST = InterfaceST
        VLAN = InterfaceVlan
        VME = InterfaceVME
        INTERFACE_RANGE = InterfaceInterRange
