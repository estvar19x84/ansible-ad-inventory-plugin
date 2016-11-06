import os
import argparse
import sys
import ConfigParser
import ldap
import json


class EnvironmentSettings:

    ldapUri = ''
    serverBase = ''
    bindUser = ''
    bindPassword = ''
    anonymous = ''
    criteria = ''
    attribute = ''
    group_by = ''

    def __init__(self):
        self.get_runtime_variables()
        self.validate_environment_variables()

    # Get the required variables for execution
    # Check if the variables are defined if the .ini file exists, if not check the environment
    def get_runtime_variables(self):
        config = ConfigParser.ConfigParser()
        if (os.path.isfile(os.path.dirname(os.path.realpath(__file__)) + "/ldapinv.ini")):
            config.read(os.path.dirname(os.path.realpath(__file__)) + "/ldapinv.ini")
            self.ldapUri = config.get("connection", "LDAP_URI")
            self.serverBase = config.get("connection", "LDAP_SERVER_BASE")
            self.bindUser = config.get("connection", "LDAP_BIND_USER")
            self.bindPassword = config.get("connection", "LDAP_BIND_PASSWORD")
            self.anonymous = config.get("connection","ANONYMOUS")
            self.criteria = config.get("search","CRITERIA")
            self.attribute = config.get("search", "ATTRIBUTE")
            self.group_by = config.get("search", "GROUP_BY").split(",")
        else:
            env = os.environ
            for key,value in env.iteritems():
                # Check if LDAP_URI is defined in the environment
                if key == 'LDAP_URI':
                    self.ldapUri = value
                elif key == 'LDAP_SERVER_BASE':
                    self.serverBase = value
                elif key == 'LDAP_BIND_USER':
                    self.bindUser = value
                elif key == 'LDAP_BIND_PASSWORD':
                    self.bindPassword = value
                elif key == 'ANONYMOUS':
                    self.anonymous = value
                elif key == 'ATTRIBUTE':
                    self.anonymous = value
                elif key == 'GROUP_BY':
                    self.anonymous = value

    # Validate that all variables are defined
    def validate_environment_variables(self):
        if (self.ldapUri == "" or
            self.serverBase == "" or
            self.bindUser == "" or
            self.bindPassword == ""
        ):
            raise EnvironmentVariablesError("Error in environment settings", var_error_message)


class EnvironmentVariablesError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class AdLdapConnection:
    conn = ''
    args = ''

    def __init__(self,runtime_environment):
        self.parse_cli_args()
        self.conn = ldap.initialize(runtime_environment.ldapUri)
        if runtime_environment.anonymous:
            self.conn.simple_bind_s()
        else:
            self.conn.simple_bind_s(runtime_environment.bindUser, runtime_environment.bindPassword)

        if self.args.host:
        # data_to_print += self.get_host_info()
            d = {"_meta": {"hostvars": {}}}
            json.dumps(d, sort_keys=True, indent=2)
        else:
            print self.get_hosts()

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on ldap')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def get_hosts(self):
        d = {"_meta" : {"hostvars" : {}}}
        result_id = self.conn.search(runtime_environment.serverBase, ldap.SCOPE_SUBTREE,
                                     runtime_environment.criteria)
        result_set = []
        while 1:
            result_type, result_data = self.conn.result(result_id, 0)
            if result_data:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
            else:
                break

        # Define all keys
        for entry in result_set:
            for host,attributes in entry:
                for key, value in sorted(attributes.iteritems()):
                    if key in runtime_environment.group_by:
                        if isinstance(value,list):
                            d[value[0]] = []
                        else:
                            d[value] = []

        # Group hosts
        for entry in result_set:
            for host, attributes in entry:
                for key, value in sorted(attributes.iteritems()):
                    if key in runtime_environment.group_by:
                        instance = attributes[runtime_environment.attribute]
                        if isinstance(instance,list):
                            d[value[0]].append(instance[0])
                        else:
                            d[value[0]].append(instance)
        return json.dumps(d, sort_keys=True, indent=2)

var_error_message = "Make sure LDAP_URI, LDAP_SERVER_BASE, LDAP_BIND_USER, LDAP_BIND_PASSWORD, ATTRIBUTE and ANONYMOUS are properly defined"

# Begin execution by gathering necessary environment variables
try:
    runtime_environment = EnvironmentSettings()
    conn = AdLdapConnection(runtime_environment)
except ConfigParser.NoOptionError as err:
    print ("Error in ldapinv.ini", var_error_message )
except EnvironmentVariablesError as err:
    print ("Environment settings error:", err.expression, err.message)
except ldap.FILTER_ERROR as err:
    print ("LDAP filter error:", err.message)
except ldap.SERVER_DOWN as err:
    print ("LDAP server is down:", runtime_environment.ldapUri)
except ldap.INVALID_CREDENTIALS as err:
    print ("Invalid bind credentials for user:", runtime_environment.bindUser)
except OSError as err:
    print("OS error: {0}".format(err))
except Exception as err:
    print("Unexpected Error:", err.message)


