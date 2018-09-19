import sys
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
                str_ret += str_src[i+1].upper()
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
        {"get_attr_name":get_attr_name, "init_from_list":init_from_list})
        return cls_ret

    @staticmethod
    def init_configuration_element_default_from_list(int_index, lst_src, **kwargs):
        str_init_class_name = ConfigurationElement.generate_class_name_from_config_name(
        lst_src[0][int_index-1])
        
        for str_class_attrs in dir(kwargs["obj_caller"].__class__):
            if str_class_attrs == str_init_class_name:
                cls_to_init = getattr(kwargs["obj_caller"].__class__, str_class_attrs)
                break
        else:
            cls_to_init = ConfigurationElement.generate_configuration_elemenet_class(lst_src[0][int_index-1])
            setattr(kwargs["obj_caller"].__class__, cls_to_init.__name__, cls_to_init) 
        
        obj_attr = cls_to_init()
        obj_attr.init_from_list(int_index, lst_src, **kwargs)
        return obj_attr
    
    @staticmethod
    def init_default_from_list(obj_caller):
        def generate_init_element(int_index, lst_src, obj_caller=obj_caller, **kwargs):
            obj_ret = ConfigurationElement.init_configuration_element_default_from_list(int_index, lst_src, obj_caller=obj_caller, **kwargs)
            setattr(obj_caller, obj_ret.__class__.get_attr_name(), obj_ret)
        
        return generate_init_element
        
    @staticmethod
    def init_default_bool_from_list(obj_caller):
        """obj_caller is the one which has subclasses in it"""
        
        def generate_init_bool_element(int_index, lst_src, obj_caller=obj_caller, **kwargs):
            obj_ret = ConfigurationElement.init_configuration_element_default_from_list(int_index, lst_src, obj_caller=obj_caller, **kwargs)
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
                        raise Exception
                    
                    if len(lst_line) == int_index:
                        self.bool_active = False
                        if len(lst_src)-1 != i:
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
                str_ret += "_"+ str_current_char.lower()
            else:
                str_ret += str_current_char.lower()

        return str_ret

        
class Interface(object):
    def __init__(self, name):
        self.name = name
        self.parser = Parser()
        self.units = []    
    
    @ConfigurationElement.preprocess_deactivated_object
    def init_from_list(self, int_index, lst_src, **kwargs):
        dict_init_options = self.get_dict_init_options()
        dict_ret = self.parser.init_objects_from_list(
             int_index, lst_src, dict_init_options, **kwargs)
        
        if dict_ret:
            pdb.set_trace()
            
    def get_dict_init_options(self):
        #Each interface can edit this option to manipulate the inited objects
        dict_ret ={
                "unit": self.init_unit_from_list,
                "vlan-tagging": ConfigurationElement.init_default_bool_from_list(self),
                "description": ConfigurationElement.init_default_from_list(self),
                "gigether-options": self.init_gigether_options_from_list,
                "no-gratuitous-arp-reply": ConfigurationElement.init_default_bool_from_list(self),
                "no-gratuitous-arp-request": ConfigurationElement.init_default_bool_from_list(self),
                "aggregated-ether-options": self.init_aggregated_ether_options_from_list,
            }
        return dict_ret
    
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
        dict_ret = self.parser.init_objects_from_list(int_index, lst_src, {}, **kwargs)
        for str_unit_name, lst_lines in dict_ret.items():
            unit = Interface.Unit(str_unit_name)
            unit.init_from_list(int_index+1, lst_lines, **kwargs)
            self.units.append(unit)
    
    
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
    
    class VlanTagging_:
        def __init__(self):
            self.bool_value = None
            self.bool_active = False
        
        @ConfigurationElement.preprocess_deactivated_object
        def init_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception
            
            self.bool_value = True
        
        def get_attr_name(self):
                return "vlan_tagging"
    
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
            
        @ConfigurationElement.preprocess_deactivated_object
        def init_from_list(self, int_index, lst_src, **kwargs):
            if len(lst_src) != 1:
                raise Exception
            if lst_src[0][int_index] != "802.3ad":
                raise Exception
            
            self.protocol_802dot3ad = Interface.GigetherOptions.Protocol802dot3ad()
            self.protocol_802dot3ad.init_from_list(int_index+1, lst_src, **kwargs)
            
        class Protocol802dot3ad:
            def __init__(self):
                self.ae_interface = None
                self.parser = Parser()
                
            def init_from_list(self, int_index, lst_src, **kwargs):
                if len(lst_src) != 1:
                    raise Exception
                
                inter_ret = self.parser.get_objects_by_values({"name":lst_src[0][int_index]}, kwargs["lst_interfaces"], int_limit = 1)
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
            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src, {
                "clear-dont-fragment-bit": self.init_clear_dont_fragment_bit_from_list,
                "description": self.init_description_from_list,
                "tunnel": self.init_tunnel_from_list,
                "family": self.init_family_from_list,
                "vlan-id": self.init_vlan_id_from_list,
                }, 
                **kwargs)
            if dict_ret:
                pdb.set_trace()
            
        def init_vlan_id_from_list(self, int_index, lst_src, **kwargs):
            self.vlan_id = Interface.Unit.VlanIdValue()
            self.vlan_id.init_from_list(int_index, lst_src, **kwargs)
            
        def init_default_from_list(self, int_index, lst_src, **kwargs):
            self.dict_vars_vals[lst_src[0][int_index-1]]= lst_src

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
                }, 
                **kwargs)
                
                if dict_ret:
                    pdb.set_trace()
                
            def init_inet6_from_list(self, int_index, lst_src, **kwargs):
                self.protocol = Interface.Unit.Family.Inet()
                self.protocol.init_from_list(int_index, lst_src, **kwargs)            
            
            def init_inet_from_list(self, int_index, lst_src, **kwargs):
                self.protocol = Interface.Unit.Family.Inet6()
                self.protocol.init_from_list(int_index, lst_src, **kwargs)
                
            class Inet:
                def __init__(self):
                    self.mtu = None
                    self.addresses = []
                    self.parser = Parser()
                    self.dict_vars_vals = OrderedDict()
                
                @ConfigurationElement.preprocess_deactivated_object
                def init_from_list(self, int_index, lst_src, **kwargs):
                    #for 
                    dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src, {
                    "mtu": self.init_mtu_from_list,
                    "address": self.init_address_from_list,
                    "filter": self.init_default_from_list,
                    "sampling": self.init_default_from_list,
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
                    dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src, {}, 
                    **kwargs)
                    
                    for str_key, lst_lines in dict_ret.items():
                        address = self.Address()
                        address.init_from_list(int_index, lst_lines, **kwargs)
                        self.addresses.append(address)
                
                def init_default_from_list(self, int_index, lst_src, **kwargs):
                    for lst_line in lst_src:
                        self.dict_vars_vals[" ".join(lst_line)] = int_index
                
                class Address:
                    def __init__(self):
                        self.ip_address = None
                        
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        if len(lst_src) != 1:
                            pdb.set_trace()

                        ip = IP()
                        ip.init_address(lst_src[0][int_index])

                    class Address_Value:
                        def __init__(self):
                            pass
                            
                        def init_from_list(self, lst_src):
                            pdb.set_trace()
            
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
                    "filter": self.init_default_from_list,
                    "sampling": self.init_default_from_list,
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
                    dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src, {}, 
                    **kwargs)
                    
                    for str_key, lst_lines in dict_ret.items():
                        address = self.Address()
                        address.init_from_list(int_index, lst_lines, **kwargs)
                        self.addresses.append(address)
                
                def init_default_from_list(self, int_index, lst_src, **kwargs):
                    for lst_line in lst_src:
                        self.dict_vars_vals[" ".join(lst_line)] = int_index
                
                class Address:
                    def __init__(self):
                        self.value = None
                        self.parser = Parser()
                        
                    @ConfigurationElement.preprocess_deactivated_object
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        if len(lst_src) < 1:
                            raise Exception
                        
                        self.value = self.__class__.Address_Value()
                        self.value.init_from_list(int_index+1, lst_src, **kwargs)
                        
                    class Address_Value:
                        def __init__(self):
                            self.value = None
                            self.parser = Parser()
                        
                        @ConfigurationElement.preprocess_deactivated_object
                        def init_from_list(self, int_index, lst_src, **kwargs):
                            self.value = IP()
                            self.value.init_address(lst_src[0][int_index-1])
                            #pdb.set_trace()
                            dict_ret = self.parser.init_objects_from_list(
                            int_index, lst_src, 
                            {
                            "primary":ConfigurationElement.init_default_bool_from_list(self),
                            "preferred":ConfigurationElement.init_default_bool_from_list(self),
                            }, 
                            **kwargs)
                            
                            if dict_ret:
                                pdb.set_trace()
                                raise Exception
                    
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
        
        
class InterfaceME(Interface):
    def __init__(self, name):
        super().__init__(name)
        
    
class JuniperBaseDevice(object):
    def __init__(self):
        self.parser = Parser()
        self.interfaces = []
        
    #def init_deactivated_object(self, 
    #@init_deactivated_object
    def init_from_list(self, lst_src, int_index=1):
        self.lst_src = lst_src
        
        dict_ret = self.parser.init_objects_from_list(
             int_index, lst_src, 
            {
                "version": self.init_version_from_list,
                "interfaces": self.init_interfaces_from_list,
                "configuration": ConfigurationElement.init_default_from_list(self),
                "groups": ConfigurationElement.init_default_from_list(self),
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
            }
            )
        
        if dict_ret:
            pdb.set_trace()
            
    def init_configuration_from_list(self, lst_src):
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
            return 1
            
        lst_ordered_src = sorted(list(dict_src.keys()), key = func_key)
        
        for str_name in lst_ordered_src:
            lst_lines = dict_src[str_name]
            self.init_and_append_interface(str_name, int_index+1, lst_lines)
        
    def init_and_append_interface(self, str_name, int_index, lst_lines):
        for type_interface in JuniperBaseDevice.InterfaceType:
            if str_name.startswith(type_interface.name.lower()):
                cls_inter = type_interface.value
                break
        else:
            pdb.set_trace()
            raise Exception
        
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
    
    def init_protocols_from_list(self, lst_src):
        pdb.set_trace()
    
    def init_policy_options_from_list(self, lst_src):
        pdb.set_trace()
    
    def init_firewall_from_list(self, lst_src):
        pdb.set_trace()
    
    def init_routing_instances_from_list(self, lst_src):
        pdb.set_trace()
        
    class InterfaceType(Enum):
        LO = InterfaceLo
        FXP = InterfaceFXP
        GE = InterfaceGE
        XE = InterfaceXE
        GR = InterfaceGR
        AE = InterfaceAE
        ME = InterfaceME
        
    
    
    
    