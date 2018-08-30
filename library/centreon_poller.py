#!/usr/bin/python
# -*- coding: utf-8 -*-

# import module snippets
from ansible.module_utils.basic import *

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '0.1',
    'version': '0.1'
}

DOCUMENTATION = '''
---
module: centreon_poller
version_added: "2.2"
short_description: applycfg on poller

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
  instance:
    description:
      - Poller instance to check host
    default: Central
  action:
    description:
      - action for poller
    default: applycfg
    choices: ['applycfg']
requirements:
  - Python Centreon API
author:
    - Guillaume Watteeux
'''

EXAMPLES = '''
# Add host
 - centreon_poller:
     url: 'https://centreon.company.net/centreon'
     username: 'ansible_api'
     password: 'strong_pass_from_vault'
     instance: Central
     action: applycfg
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
            instance=dict(default='Central'),
            action=dict(default='applycfg', choices=['applycfg']),
        )
    )

    if not centreonapi_found:
        module.fail_json(msg="Python centreonapi module is required")

    url = module.params["url"]
    username = module.params["username"]
    password = module.params["password"]
    instance = module.params["instance"]
    action = module.params["action"]

    has_changed = False

    try:
        centreon = Centreon(url, username, password)
    except Exception as exc:
        module.fail_json(
            msg="Unable to connect to Centreon API: %s" % exc.message
        )

    if not centreon.exists_poller(instance):
        module.fail_json(msg="Poller '%s' does not exists" % instance)

    try:
        if action == "applycfg":
            centreon.poller.applycfg(instance)
            has_changed = True
    except Exception as exc:
        module.fail_json(msg='%s' % exc.message)

    module.exit_json(changed=has_changed)


if __name__ == '__main__':
    main()
