import sys
import pdb
from collections import OrderedDict
from enum import Enum

from src.parser import Parser


class Interface(object):
    def __init__(self, name, logger):
        self.name = name
        self.logger = logger
        self.parser = Parser(logger)
        
    def init_from_list(self, int_index, lst_src, **kwargs):
        dict_init_options = self.get_dict_init_options()
        dict_ret = self.parser.init_objects_from_list(
             int_index, lst_src, dict_init_options, **kwargs) 

    def get_dict_init_options(self):
        dict_ret ={
                "unit": self.init_unit_from_list,
                "vlan-tagging": self.init_vlan_tagging_from_list
            }
        return dict_ret
    
    def init_vlan_tagging_from_list(self, int_src, lst_src, **kwargs):
        for lst_line in lst_src:
            if lst_line[0] != "set": 
                raise Exception
            
            if len(lst_line) > 4:
                pdb.set_trace()
                raise Exception
    
    def init_unit_from_list(self, int_index, lst_src, **kwargs):
        dict_ret = self.parser.init_objects_from_list(int_index, lst_src, {}, **kwargs)
        pdb.set_trace()
        
    
class InterfaceLo(Interface):
    pass
    
    
class InterfaceFXP(Interface):
    pass        

    
class InterfaceGE(Interface):
    def __init__(self, name, logger):
        super().__init__(name, logger)

        
    
class JuniperBase(object):
    def __init__(self, logger):
        self.logger = logger
        self.parser = Parser(logger)
    
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
        for type_interface in JuniperBase.InterfaceType:
            if str_name.startswith(type_interface.name.lower()):
                cls_inter = type_interface.value
                break
        else:
            pdb.set_trace()
            raise Exception
        
        interface = cls_inter(str_name, self.logger)
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
        
    
    
    
    