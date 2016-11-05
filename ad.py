import os
import sys
import ConfigParser
import ldap

class EnvironmentSettings:

    ldapUri = ''
    serverBase = ''
    bindUser = ''
    bindPassword = ''

    def __init__(self):
        self.get_runtime_variables()
        self.validate_environment_variables()

    # Get the required variables for execution
    # Check if the variables are defined if the .ini file exists, if not check the environment
    def get_runtime_variables(self):
        config = ConfigParser.ConfigParser()
        if os.path.isfile("ad.ini"):
            config.read("ad.ini")
            self.ldapUri = config.get("connection", "AD_LDAP_URI")
            self.serverBase = config.get("connection", "AD_LDAP_SERVER_BASE")
            self.bindUser = config.get("connection", "AD_LDAP_BIND_USER")
            self.bindPassword = config.get("connection", "AD_LDAP_BIND_PASSWORD")
        else:
            env = os.environ
            for key,value in env.iteritems():
                # Check if AD_LDAP_URI is defined in the environment
                if key == 'AD_LDAP_URI':
                    self.ldapUri = value
                elif key == 'AD_LDAP_SERVER_BASE':
                    self.serverBase = value
                elif key == 'AD_LDAP_BIND_USER':
                    self.bindUser = value
                elif key == 'AD_LDAP_BIND_PASSWORD':
                    self.bindPassword = value

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

    def __init__(self,runtime_environment):
        self.conn = ldap.initialize(runtime_environment.ldapUri)
        self.conn.simple_bind_s(runtime_environment.bindUser, runtime_environment.bindPassword)

    def get_computers(self):
        criteria = "(&(objectClass=computer))"


var_error_message = "Make sure AD_LDAP_URI, AD_LDAP_SERVER_BASE, AD_LDAP_BIND_USER and AD_LDAP_BIND_PASSWORD are properly defined"

# Begin execution by gathering necessary environment variables
try:
    runtime_environment = EnvironmentSettings()
    conn = AdLdapConnection(runtime_environment)
except ConfigParser.NoOptionError as err:
    print ("Error in ad.ini", var_error_message )
except EnvironmentVariablesError as err:
    print ("Environment settings error:", err.expression, err.message)
except ldap.SERVER_DOWN as err:
    print ("LDAP server is down:", runtime_environment.ldapUri)
except ldap.INVALID_CREDENTIALS as err:
    print ("Invalid bind credentials for user:", runtime_environment.bindUser)
except OSError as err:
    print("OS error: {0}".format(err))
except:
    print("Unexpected Error:", sys.exc_info()[0])


