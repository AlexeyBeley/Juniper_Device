import sys
import pdb
from collections import OrderedDict
from enum import Enum

from src.ip import IP
from src.parser import Parser


class Interface(object):
    def __init__(self, name):
        self.name = name
        self.parser = Parser()
        self.units = []    
          
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
                "vlan-tagging": self.init_vlan_tagging_from_list
            }
        return dict_ret
    
    def init_vlan_tagging_from_list(self, int_src, lst_src, **kwargs):
        for lst_line in lst_src:
            if lst_line[0] != "set": 
                raise Interface.InterfaceInitException
            
            if len(lst_line) > 4:
                pdb.set_trace()
                raise Interface.InterfaceInitException
    
    def init_unit_from_list(self, int_index, lst_src, **kwargs):
        dict_ret = self.parser.init_objects_from_list(int_index, lst_src, {}, **kwargs)
        for str_unit_name, lst_lines in dict_ret.items():
            unit = Interface.Unit(str_unit_name)
            unit.init_from_list(int_index+1, lst_lines, **kwargs)
            self.units.append(unit)
    
    class Unit(object):
        def __init__(self, name):
            self.name = name
            self.parser = Parser()
            self.dict_vars_vals = {}
            
        def init_from_list(self, int_index, lst_src, **kwargs):
            dict_ret = self.parser.init_objects_from_list(
                int_index, lst_src, {
                "clear-dont-fragment-bit": self.init_clear_dont_fragment_bit_from_list,
                "description": self.init_description_from_list,
                "tunnel": self.init_tunnel_from_list,
                "family": self.init_family_from_list,
                }, 
                **kwargs)
            if dict_ret:
                pdb.set_trace()
            
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
                
            self.description = lst_src[0][int_index]
        
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
                self.protocol = Interface.Unit.Family.Inet()
                self.protocol.init_from_list(int_index, lst_src, **kwargs)
                
            class Inet:
                def __init__(self):
                    self.mtu = None
                    self.addresses = []
                    self.parser = Parser()
                
                def init_from_list(self, int_index, lst_src, **kwargs):
                    dict_ret = self.parser.init_objects_from_list(
                    int_index, lst_src, {
                    "mtu": self.init_mtu_from_list,
                    "address": self.init_address_from_list,
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
                    
                    if len(list(dict_ret.keys())) != 1:
                        pdb.set_trace()
                    
                    for str_key, lst_lines in dict_ret.items():
                        address = self.Address()
                        address.init_from_list(int_index, lst_lines, **kwargs)
                        self.addresses.append(address)
                    
                class Address:
                    def __init__(self):
                        self.ip_address = None
                        
                    def init_from_list(self, int_index, lst_src, **kwargs):
                        if len(lst_src) != 1:
                            pdb.set_trace()

                        ip = IP()
                        ip.init_address(lst_src[0][int_index])

                        
                        
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
    
    #def init_deactivated_object(self, 
    #@init_deactivated_object
    def init_from_list(self, lst_src, int_index=1):
        self.lst_src = lst_src
        
        dict_ret = self.parser.init_objects_from_list(
             int_index, lst_src, 
            {
                "version": self.init_version_from_list,
                "interfaces": self.init_interfaces_from_list
            }
            )
        
        if dict_ret:
            self.dict_vars_vals = dict_ret
            
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
        
        for str_name, lst_lines in dict_src.items():
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
        interface.init_from_list(int_index, lst_lines)
        
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
        
    
    
    
    