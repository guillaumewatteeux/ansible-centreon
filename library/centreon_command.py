#!/usr/bin/python
# -*- coding: utf-8 -*-

# import module snippets
from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0',
    'version': '1.0'
}

DOCUMENTATION = '''
---
module: centreon_command
version_added: "2.8"
description: Manage Centreon commands.
short_description: Manage Centreon commands

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
      - Poller instance
    default: Central
  applycfg:
    description:
      - Applycfg on poller
    default: True
    choices: ['True','False']
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
            instance=dict(list(), default='Central'),
            name=dict(required=True),
            type=dict(default='check', choices=['check', 'notif', 'misc', 'discovery']),
            line=dict(default=None),
            graph=dict(default=None),
            example=dict(default=None),
            comment=dict(default=None),
            applycfg=dict(default=True, type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
            validate_certs=dict(default=True, type='bool'),
        )
    )

    if not centreonapi_found:
        module.fail_json(msg="Python centreonapi >= 0.1.3 module is required")

    url = module.params["url"]
    username = module.params["username"]
    password = module.params["password"]
    instance = module.params["instance"]
    name = module.params["name"]
    type = module.params["type"]
    line = module.params["line"]
    graph = module.params["graph"]
    example = module.params["example"]
    comment = module.params["comment"]
    applycfg = module.params["applycfg"]
    state = module.params["state"]
    validate_certs  = module.params["validate_certs"]

    has_changed = False

    try:
        centreon = Centreon(url, username, password, check_ssl=validate_certs)
    except Exception as e:
        module.fail_json(
            msg="Unable to connect to Centreon API: %s" % e.message
        )

    try:
        st, poller = centreon.pollers.get(instance)
    except Exception as e:
        module.fail_json(msg="Unable to get pollers: {}".format(e.message))

    if not st and poller is None:
        module.fail_json(msg="Poller '%s' does not exists" % instance)
    elif not st:
        module.fail_json(msg="Unable to get poller list %s " % poller)

    cmd_state, cmd = centreon.commands.get(name)

    if centreon.commands.exist(name) and state == "absent":
        centreon.command.delete(name)
        has_changed = True
        if applycfg:
            centreon.pollers.applycfg(instance)
        module.exit_json(
            changed=has_changed, result="Command %s deleted" % name)

    if not centreon.commands.exist(name) and state == "present":
        try:
            centreon.commands.add(
                name,
                type,
                line
            )
        except Exception as e:
            module.exit_json(msg='%s' % e.message)

    try:
        command = centreon.commands.get(name)
        if type != command.type:
            command.setparam('type', type)
            has_changed = True

        if line != command.line:
            command.setparam('line', line)
            has_changed = True

        if graph:
            command.setparam('graph', graph)
            has_changed = True

        if example:
            command.setparam('example', example)
            has_changed = True

        if comment:
            command.setparam('comment', comment)
            has_changed = True
    except Exception as e:
        module.fail_json(msg='%s' % e.message)

    try:
        if applycfg:
            centreon.pollers.applycfg(instance)
            has_changed = True
    except Exception as exc:
        module.fail_json(msg='%s' % exc.message)

    module.exit_json(changed=has_changed, msg=data)


if __name__ == '__main__':
    main()
