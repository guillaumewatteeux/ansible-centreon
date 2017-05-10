#!/usr/bin/python
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = { 'status': ['preview'],
                     'supported_by': 'community',
                     'version': '0.1'}

DOCUMENTATION = '''
---
module: centreon_host
short_description: add host to centreon

options:
  url:
    description:
      - Centreon URL
    required: True
  username:
    description:
      - Centreon API username
    required: True
  password:
    description:
      - Centreon API username's password
    required: True
  name:
    description:
      - Hostname
    required: True
  hosttemplates:
    description:
      - Host Template list for this host
  alias:
    description:
      - Host alias
    default: name params
  ipaddr:
    description:
      - IP address
  instance:
    description:
      - Poller instance to check host
    default: Central
  hostgroups:
    description:
      - Hostgroups list
  params:
    description:
      - Config specific parameter (dict)
  macros:
    description:
      - Set Host Macros (dict)
  state:
    description:
      - Create / Delete host on Centreon
    default: present
    choices: ['present', 'absent']
  status:
    description:
      - Enable / Disable host on Centreon
    default: enabled
    choices: ['enabled', 'disabled']
author:
    - Guillaume Watteeux
'''

EXAMPLES = '''
# Add host
 - centreon_host:
     url: 'https://centreon.company.net/centreon'
     username: 'ansible_api'
     password: 'strong_pass_from_vault'
     name: "{{ ansible_fqdn }}"
     alias: "{{ ansible_hostname }}"
     ipaddr: "{{ ansible_default_ipv4.address }}"
     hosttemplates:
       - OS-Linux-SNMP-custom
       - OS-Linux-SNMP-disk
     hostgroups:
       - Linux-Servers
       - Production-Servers
       - App1
     instance: Central
     status: enabled
     state: present:
     params:
       notes_url: "https://wiki.company.org/servers/{{ ansible_fqdn }}"
       notes: "My Best server"
     macros:
       MACRO1: value1
       MACRO2: value2
'''

# =============================================
# Centreon module API Rest
#

# import module snippets
from ansible.module_utils.basic import *

try:
    from centreonapi.centreon import Centreon
except ImportError:
    centreonapi_found = False
else:
    centreonapi_found = True



def main():

    module = AnsibleModule(
        argument_spec=dict(
            url=dict(required=True),
            username=dict(default='admin', no_log=True),
            password=dict(default='centreon', no_log=True),
            name=dict(required=True),
            hosttemplates=dict(type='list'),
            alias=dict(default=None),
            ipaddr=dict(),
            instance=dict(default='Central'),
            hostgroups=dict(type='list'),
            params=dict(type='dict'),
            macros=dict(type='dict'),
            state=dict(default='present', choices=['present', 'absent']),
            status=dict(default='enabled', choices=['enabled', 'disabled']),
        )
    )

    if not centreonapi_found:
        module.fail_json(msg="Python centreonapi module is required")

    url = module.params["url"]
    username = module.params["username"]
    password = module.params["password"]
    name = module.params["name"]
    alias = module.params["alias"]
    ipaddr = module.params["ipaddr"]
    hosttemplates = module.params["hosttemplates"]
    instance = module.params["instance"]
    hostgroups = module.params["hostgroups"]
    params = module.params["params"]
    macros = module.params["macros"]
    state = module.params["state"]
    status = module.params["status"]

    try:
        centreon = Centreon(url, username, password)
    except Exception as exc:
        module.fail_json(msg="Unable to connect to Centreon API: %s" % exc.message)

    if alias is None:
        alias = name

    if not centreon.exists_poller(instance):
        module.fail_json(msg="Poller '%s' does not exists" % instance)

    # On exist host -------------
    #
    if centreon.exists_host(name):
        if state == "absent":
            try:
                centreon.host.delete(name)
                centreon.poller.applycfg(instance)
                module.exit_json(changed=True, mode="delete")
            except Exception as exc:
                module.fail_json(msg='State: %s' % exc.message)

        try:
            # Check Properties
            for h in centreon.host_list():
                if h.name == name:
                    host = h

            if status == "disabled" and int(host.state) == 1:
                centreon.host.disable(name)
            if status == "enabled" and int(host.state) == 0:
                centreon.host.enable(name)

            if not host.address == ipaddr:
                centreon.host.setparameters(name, 'address', ipaddr)

            if not host.alias == alias:
                centreon.host.setparameters(name, 'alias', alias)

            centreon.host.sethostgroup(name, hostgroups)
            centreon.host.settemplate(name, hosttemplates)

            if macros:
                for k in macros.keys():
                    centreon.host.setmacro(name, k, macros.get(k))

            if params:
                for k in params.keys():
                    centreon.host.setparameters(name, k, params.get(k))

            centreon.host.applytemplate(name)
            centreon.poller.applycfg(instance)
            module.exit_json(changed=True, mode="done")
        except Exception as exc:
            module.fail_json(msg='%s' % exc.message)

    else:
        try:
            centreon.host.add(name,
                          alias,
                          ipaddr,
                          hosttemplates,
                          instance,
                          hostgroups)
            # Apply the host templates for create associate services
            centreon.host.applytemplate(name)
            # Apply Centreon configuration and reload the engine
            centreon.poller.applycfg(instance)
            module.exit_json(changed=True)

        except Exception as exc:
            module.fail_json(msg='Create: %s' % exc.message)

if __name__ == '__main__':
    main()


