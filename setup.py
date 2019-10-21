#!/usr/bin/env python3

import requests
import urllib3
import json
import sys
import getpass
import socket
from jinja2 import Template
from requests.exceptions import HTTPError, RequestException

datacenter_map = {
    'local': {
        'consul_url': "http://localhost:8500",
        'vault_url': "http://localhost:8200",
        'consul_server': 'localhost'
    },
    'bk' : {
        'consul_url': "http://bkconsul.agoda.local:8500",
        'vault_url': "https://bk.dev-vault.agoda.local:8200",
        'consul_server': 'bkconsul.agoda.local'
    },
    'qa1' : {
        'consul_url': "http://qa1consul.agoda.local:8500",
        'vault_url': "https://hk.qa-vault.agoda.local:8200",
        'consul_server': 'qa1consul.agoda.local'
    },
    'hk' : {
        'consul_url': "http://hkconsul.agoda.local:8500",
        'vault_url': "https://hk.vault.agoda.local:8200",
        'consul_server': 'hkconsul.agoda.local'
    },
    'sg' : {
        'consul_url': "http://sgconsul.agoda.local:8500",
        'vault_url': "https://sg.vault.agoda.local:8200",
        'consul_server': 'sgconsul.agoda.local'
    },
    'sh' : {
        'consul_url': "http://shconsul.agoda.local:8500",
        'vault_url': "https://sh.vault.agoda.local:8200",
        'consul_server': 'shconsul.agoda.local'
    },
    'am' : {
        'consul_url': "http://amconsul.agoda.local:8500",
        'vault_url': "https://am.vault.agoda.local:8200",
        'consul_server': 'amconsul.agoda.local'
    },
    'as' : {
        'consul_url': "http://asconsul.agoda.local:8500",
        'vault_url': "https://as.vault.agoda.local:8200",
        'consul_server': 'asconsul.agoda.local'
    }
}

def get_request(url, headers):
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  
    except RequestException as err:
        print(f'Other error occurred: {err}') 
    else:
        return response
    return None

def put_request(url, data=None, headers=None):
    response = requests.put(url, data=data, headers=headers, verify=False)
    response.raise_for_status()
    return response

def post_request(url, data=None, headers=None):
    response = requests.put(url, data=data, headers=headers, verify=False)
    response.raise_for_status()
    return response

class Vault:
    def __init__(self, vault_url: str, vault_token: str):
        self.vault_url = vault_url
        self.vault_token = vault_token

    def default_headers(self):
        return {'X-Vault-Token': self.vault_token }
    
    def generate_consul_token(self, consul_role):
        response = get_request(
            self.vault_url + "/v1/consul/creds/" + consul_role,
            headers=self.default_headers()
        )
        if response != None:
            json_response = response.json()
            if 'data' in json_response and 'token' in json_response['data']:
                return json_response['data']['token']
        return None

    def get_policy(self, policy_name):
        response = get_request(
            self.vault_url + "/v1/sys/policy/" + policy_name,
            headers=self.default_headers()
        )
        if response != None:
            json_response = response.json()
            if 'rules' in json_response:
                return json_response
        return None
    
    def get_role_id(self, approle_name):
        role_id_response = get_request(
            self.vault_url + "/v1/auth/approle/role/" + approle_name + "/role-id",
            headers=self.default_headers()
        ).json()
        if 'data' in role_id_response and 'role_id' in role_id_response['data']:
            return role_id_response['data']['role_id']
        return None

    def get_secret_id(self, approle_name):
        secret_id_response = post_request(
            self.vault_url + "/v1/auth/approle/role/" + approle_name + "/secret-id",
            headers=self.default_headers()
        ).json()
        if 'data' in secret_id_response and 'secret_id' in secret_id_response['data']:
            return secret_id_response['data']['secret_id']
        return None

    def approle_login(self, role_id, secret_id):
        login_response = post_request(
            self.vault_url + "/v1/auth/approle/login",
            data=json.dumps({
                'role_id': role_id,
                'secret_id': secret_id
            })
        ).json()
        if 'auth' in login_response and 'client_token' in login_response['auth']:
            return login_response['auth']['client_token']
        return None
        
    def ldap_login(self, username, password):
        login_response = post_request(
            self.vault_url + "/v1/auth/ldap/login/" + username,
            data=json.dumps({'password': password})
        ).json()
        if 'auth' in login_response and 'client_token' in login_response['auth']:
            return login_response['auth']['client_token']
        return None

def read_template(file):
    policy_template = ""
    f=open("./" + file, "r")
    if f.mode == 'r':
        policy_template = f.read()
    else:
        print("Couldn't read consul team policy template file")
        sys.exit(2)
    return Template(policy_template)

def main(args):
    datacenter = input("Datacenter : ")
    ldap_user = input("LDAP Username : ")
    ldap_password = getpass.getpass("LDAP Password(Hidden) : ")
    team_name = input("LDAP Team Group : ")
    service_name = input("Which service do you want to connect to : ")
    local_bind_port = input("Connect on which port : ")
    vault_url = datacenter_map[datacenter]['vault_url']
    consul_url = datacenter_map[datacenter]['consul_url']
    vault = Vault(vault_url, "")
    vault_token = vault.ldap_login(ldap_user, ldap_password)

    vault.vault_token = vault_token
    consul_token = vault.generate_consul_token(team_name.lower() + '_team_cpolicy')
    if consul_token == None:
        print("Your consul+vault policy is probably not setup. Please contact devopsmonkey@agoda.com")
        exit(1)
    else:
        print("Generating your .env now. You should run `docker-compose up -d` now")
        hostname = socket.gethostname()    
        ip_address = socket.gethostbyname(hostname)

        consul_server = datacenter_map[datacenter]['consul_server']
        consul_env = read_template(".env.j2").render(
            datacenter=datacenter,
            consul_server=consul_server, 
            private_ip=ip_address, 
            operator="operator-"+team_name, 
            upstream=service_name, 
            local_bind_port=local_bind_port
        )
        f = open(".env", "w")
        f.write(consul_env)
        f.close()

        consul_config = read_template("config.hcl.j2").render(
            token=consul_token
        )
        f = open("config.hcl", "w")
        f.write(consul_config)
        f.close()

if __name__ == "__main__":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    requests.packages.urllib3.disable_warnings()

    main(sys.argv)