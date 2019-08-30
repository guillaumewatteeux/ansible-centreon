#!/usr/bin/python
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = { 'status': ['preview'],
                     'supported_by': 'community',
                     'metadata_version': '0.1',
                     'version': '0.1'}

DOCUMENTATION = '''


'''

EXAMPLES = '''

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
            name=dict(default=None),
            host=dict(required=True),
            servicetemplate=dict(default=None),
            description=dict(default=None),
            param=dict(type='list', default=None),
            macros=dict(type='list', default=None),
            instance=dict(default='Central'),
            state=dict(default='present', choices=['present','absent']),
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
    host = module.params["host"]
    servicetemplate = module.params["servicetemplate"]
    description = module.params["description"]
    params = module.params["params"]
    macros = module.params["macros"]
    instance = module.params["instance"]
    state = module.params["state"]
    status = module.params["status"]
    applycfg = module.params["applycfg"]

    has_changed = False

    try:
        centreon = Centreon(url, username, password)
    except Exception as e:
        module.fail_json(msg="Unable to cpnnect to Centreon API: %s" % e.message)

    try:
        if not centreon.exists_poller(instance):
            module.fail_json(msg="Poller '%s' does not exists" % instance)
    except Exception:
        module.fail_json(msg="Unable to get poller list")

    # on exist service ------
    data = []
