#!/usr/bin/python
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = { 'status': ['preview'],
                     'supported_by': 'community',
                     'version': '0.1'}

DOCUMENTATION = '''
---
module: centreon_add_host
short_description: add host to centreon
author:
    - Guillaume Watteeux
'''

EXAMPLES = '''

'''

# =============================================
# Centreon module API Rest
#

# import module snippets
from ansible.module_utils.basic import *
from centreonapi.centreon import Centreon


def main():

    module = AnsibleModule(
        argument_spec=dict(
            url=dict(required=True),
            username=dict(default="admin", no_log=True),
            password=dict(default="centreon", no_log=True),
            name=dict(required=True),
            hosttemplates=dict(),
            alias=dict(default=None),
            ipaddr=dict(),
            instance=dict(default="Central"),
            hostgroups=dict(),
            state=dict(default="present", choices=['present', 'absent']),
            status=dict(default="enabled", choices=['enabled', 'disabled']),
        )
    )

    url = module.params["url"]
    username = module.params["username"]
    password = module.params["password"]
    name = module.params["name"]
    alias = module.params["alias"]
    ipaddr = module.params["ipaddr"]
    hosttemplates = module.params["hosttemplates"]
    instance = module.params["instance"]
    hostgroups = module.params["hostgroups"]

    centreon = Centreon(url, username, password)

    if alias is None:
        alias = name

    if not centreon.exists_poller(instance):
        module.fail_json(msg="Poller '%s' does not exists" % instance)

    if not centreon.exists_hostgroups(hostgroups):
        module.fail_json(msg="Hostgroup '%s' does not exist" % hostgroups)

    if not centreon.exists_hosttemplates(hosttemplates):
        module.fail_json(msg="HostTemplate '%s' does not exist" % hosttemplates)

    if not centreon.exists_host(name):
        print("add Host %s" % name)
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
    else:
        # TODO: set hostgroups, templates, instances...
        module.exit_json(changed=False)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()


