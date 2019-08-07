#!/usr/bin/python
# -*- coding: utf-8 -*-

# import module snippets
from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '0.1',
    'version': '0.1'}

DOCUMENTATION = '''
---
module: centreon_hostgroup
version_added: "2.2"
description: Manage Centreon hostgroupups.
short_description: Manage Centreon hostgroupups

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
  hg:
    description:
      - Hostgroup name (/ alias)
  state:
    description:
      - Create / Delete hostgroup
    default: present
    choices: ['present', 'absent']
  validate_certs:
    type: bool
    default: yes
    description:
      - If C(no), SSL certificates will not be validated.
requirements:
  - Python Centreon API
author:
    - Guillaume Watteeux
'''

EXAMPLES = '''
# Add host
- centreon_hostgroup:
    url: 'https://centreon.company.net/centreon'
    username: 'ansible_api'
    password: 'strong_pass_from_vault'
    hg:
      - name: Linux-Servers
        alias: Linux Server
      - name: project_1
    state: present

# Delete host
- centreon_hostgroup:
    url: 'https://centreon.company.net/centreon'
    username: 'ansible_api'
    password: 'strong_pass_from_vault'
    hg:
      name: Linux-Serveur
    state: absent
'''

# =============================================
# Centreon module API Rest
#

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
            hg=dict(required=True, type='list'),
            state=dict(default='present', choices=['present', 'absent']),
            validate_certs=dict(default=True, type='bool'),
        )
    )

    if not centreonapi_found:
        module.fail_json(msg="Python centreonapi module is required")

    url = module.params["url"]
    username = module.params["username"]
    password = module.params["password"]
    name = module.params["hg"]
    state = module.params["state"]
    validate_certs = module.params["validate_certs"]

    has_changed = False

    try:
        centreon = Centreon(url, username, password, check_ssl=validate_certs)
    except Exception as e:
        module.fail_json(
            msg="Unable to connect to Centreon API: %s" % e.message
        )

    try:
        hostgroups = centreon.hostgroups.list()
    except Exception as e:
        module.fail_json(msg="Unable to list hostgroups: {}".format(e.message))

    if state == "absent":
        for hg in name:
            if hg.get('name') in hostgroups.keys():
                s, h = centreon.hostgroups.delete(hg.get('name'))
                if s:
                    has_changed = True
                else:
                    module.fail_json(msg="Unable to delete hostgroup: %s" % h)
        if has_changed:
            module.exit_json(msg="Hostgroups deleted %s" % hostgroups, changed=has_changed)

    else:
        for hg in name:
            if hg.get('name') not in hostgroups.keys():
                if hg.get('alias') is None:
                    alias = hg.get('name')
                else:
                    alias = hg.get('alias')
                s, h = centreon.hostgroups.add(hg.get('name'), alias)
                if s:
                    has_changed = True
                else:
                    module.fail_json(msg="Unable to create hostgroup: %s" % h)

        if has_changed:
            module.exit_json(msg="Hostgroups created", changed=has_changed)

    module.exit_json(changed=has_changed)

if __name__ == '__main__':
    main()
