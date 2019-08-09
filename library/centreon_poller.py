#!/usr/bin/python
# -*- coding: utf-8 -*-

# import module snippets
from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '0.2',
    'version': '0.2'
}

DOCUMENTATION = '''
---
module: centreon_poller
version_added: "2.2"
description: Deploy configuration to a Centreon poller.
short_description: Deploy configuration to a Centreon poller

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
            validate_certs=dict(default=True, type='bool'),
        )
    )

    if not centreonapi_found:
        module.fail_json(msg="Python centreonapi module is required")

    url = module.params["url"]
    username = module.params["username"]
    password = module.params["password"]
    instance = module.params["instance"]
    action = module.params["action"]
    validate_certs = module.params["validate_certs"]

    has_changed = False

    try:
        centreon = Centreon(url, username, password, check_ssl=validate_certs)
    except Exception as exc:
        module.fail_json(
            msg="Unable to connect to Centreon API: %s" % exc.message
        )

    try:
        st, poller = centreon.pollers.get(instance)
    except Exception as e:
        module.fail_json(msg="Unable to get pollers: {}".format(e.message))

    if not st and poller is None:
        module.fail_json(msg="Poller '%s' does not exists" % instance)
    elif not st:
        module.fail_json(msg="Unable to get poller list %s " % poller)

    if action == "applycfg":
        s, p = poller.applycfg()
        if s:
            has_changed = True
            module.exit_json(msg="Applied config on poller", changed=has_changed)
        else:
            module.fail_json(msg=p)

    module.exit_json(changed=has_changed)


if __name__ == '__main__':
    main()
