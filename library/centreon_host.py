#!/usr/bin/python
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = { 'status': ['preview'],
                     'supported_by': 'community',
                     'metadata_version': '0.1',
                     'version': '0.1'}

DOCUMENTATION = '''
---
module: centreon_host
version_added: "2.2"
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
    type: list
  alias:
    description:
      - Host alias
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
    type: list
  hostgroups_action:
    description:
      - Define hostgroups setting method (add/set)
    default: add
    choices: ['add','set']
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
    choices: c
requirements:
  - Python Centreon API
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
            hosttemplates=dict(type='list', default=None),
            alias=dict(default=None),
            ipaddr=dict(default=None),
            instance=dict(default='Central'),
            hostgroups=dict(type='list', default=None),
            hostgroups_action=dict(default='add', choices=['add', 'set']),
            params=dict(type='list', default=None),
            macros=dict(type='list', default=None),
            state=dict(default='present', choices=['present', 'absent']),
            status=dict(default='enabled', choices=['enabled', 'disabled']),
            applycfg=dict(default=True, type='bool')
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
    hostgroups_action = module.params["hostgroups_action"]
    params = module.params["params"]
    macros = module.params["macros"]
    state = module.params["state"]
    status = module.params["status"]
    applycfg = module.params["applycfg"]

    has_changed = False

    try:
        centreon = Centreon(url, username, password)
    except Exception as e:
        module.fail_json(msg="Unable to connect to Centreon API: %s" % e.message)

    try:
        if not centreon.exists_poller(instance):
            module.fail_json(msg="Poller '%s' does not exists" % instance)
    except Exception as e:
        module.fail_json(msg="Unable to get poller list")

    # On exist host -------------
    #
    data = []
    if centreon.exists_host(name):
        if state == "absent":
            try:
                centreon.host.delete(name)
                has_changed = True
                if applycfg:
                    centreon.poller.applycfg(instance)
                module.exit_json(changed=has_changed, result="Host %s deleted" % name)
            except Exception as e:
                module.fail_json(msg='State: %s' % e.message)

        try:
            # Check Properties
            for h in centreon.host_list():
                if h.name == name:
                    host = h

            if status == "disabled" and int(host.state) == 1:
                centreon.host.disable(name)
                has_changed = True
                data.append("Host disabled")

            if status == "enabled" and int(host.state) == 0:
                centreon.host.enable(name)
                has_changed = True
                data.append("Host enabled")

            if not host.address == ipaddr and ipaddr:
                centreon.host.setparameters(name, 'address', ipaddr)
                has_changed = True
                data.append("Change ip addr: %s -> %s" % (host.address, ipaddr))

            if not host.alias == alias and alias:
                centreon.host.setparameters(name, 'alias', alias)
                has_changed = True
                data.append("Change alias: %s -> %s" % (host.alias, alias))

            hostgroups_host = centreon.host.gethostgroup(name)

            hostgroup_list = []
            for hg in hostgroups_host['result']:
                hostgroup_list.append(hg['name'])

            if hostgroups and set(hostgroups) > set(hostgroup_list):
                if hostgroups_action == "add":
                    centreon.host.addhostgroup(name, hostgroups)
                    has_changed = True
                    data.append("add hostgroups: %s" % hostgroups)
                else:
                    centreon.host.sethostgroup(name, hostgroups)
                    has_changed = True
                    data.append("set hostgroups: %s" % hostgroups)

            if hosttemplates:
                template_host = centreon.host.gettemplate(name)
                template_list = []
                for tpl in template_host['result']:
                    template_list.append(tpl['name'])

                flag_tmpl = False
                list_tmpl = []
                for tmpl in hosttemplates:
                    if tmpl not in template_list:
                        list_tmpl.append(tmpl)
                        flag_tmpl = True
                        
                if flag_tmpl:
                    centreon.host.addtemplate(name, list_tmpl)
                    centreon.host.applytemplate(name)
                    has_changed = True
                    data.append("Add HostTemplate: %s" % list_tmpl)

            if macros:
                macro_list = centreon.host.getmacro(name)
                configured_macros = {}
                for m in macro_list['result']:
                    configured_macros[m['macro name']] = m['macro value']
                for k in macros:
                    if k['name'] not in configured_macros.keys():
                        centreon.host.setmacro(name, k['name'], k['value'])
                        has_changed = True
                    else:
                        if not configured_macros.get(k['name']) == k['value']:
                            centreon.host.setmacro(name, k['name'], k['value'])
                            has_changed = True

            if params:
                for k in params:
                    centreon.host.setparameters(name, k['name'], k['value'])
                    has_changed = True

            if applycfg and has_changed:
                centreon.poller.applycfg(instance)
            module.exit_json(changed=has_changed, msg=data)
        except Exception as e:
            module.fail_json(msg='%s' % e.message)

    elif not centreon.exists_host(name) and state == "present":
        try:
            centreon.host.add(name, alias, ipaddr, hosttemplates, instance, hostgroups)
            # Apply the host templates for create associate services
            centreon.host.applytemplate(name)
            has_changed = True
            data.append("Add host: %s" % name)
            # Apply Centreon configuration and reload the engine
            if applycfg:
                centreon.poller.applycfg(instance)
            module.exit_json(changed=has_changed)
        except Exception as e:
            module.fail_json(msg='Create: %s' % e.message)
    else:
        module.exit_json(changed=has_changed)

if __name__ == '__main__':
    main()


