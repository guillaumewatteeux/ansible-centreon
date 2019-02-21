#!/usr/bin/python
# -*- coding: utf-8 -*-

# import module snippets
from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '0.3',
    'version': '0.3'
}

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
       - name: OS-Linux-SNMP-custom
       - name: OS-Linux-SNMP-disk
         state: absent
     hostgroups:
       - name: Linux-Servers
       - name: Production-Servers
       - name: App1
         state: absent
     instance: Central
     status: enabled
     state: present:
     params:
       notes_url: "https://wiki.company.org/servers/{{ ansible_fqdn }}"
       notes: "My Best server"
     macros:
       - name: MACRO1
         value: value1
         ispassword: 1
       - name: MACRO2
         value: value2
         desc: my macro
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
        argument_spec     = dict(
            url           = dict(required=True),
            username      = dict(default='admin', no_log=True),
            password      = dict(default='centreon', no_log=True),
            name          = dict(required=True),
            hosttemplates = dict(type=list, default=None),
            alias         = dict(default=None),
            ipaddr        = dict(default=None),
            instance      = dict(default='Central'),
            hostgroups    = dict(type=list, default=None),
            params        = dict(type=list, default=None),
            macros        = dict(type=list, default=None),
            state         = dict(default='present', choices=['present', 'absent']),
            status        = dict(default='enabled', choices=['enabled', 'disabled']),
            applycfg      = dict(default=True, type='bool')
        )
    )

    if not centreonapi_found:
        module.fail_json(msg="Python centreonapi module is required (>0.1.0)")

    url             = module.params["url"]
    username        = module.params["username"]
    password        = module.params["password"]
    name            = module.params["name"]
    alias           = module.params["alias"]
    ipaddr          = module.params["ipaddr"]
    hosttemplates   = module.params["hosttemplates"]
    instance        = module.params["instance"]
    hostgroups      = module.params["hostgroups"]
    params          = module.params["params"]
    macros          = module.params["macros"]
    state           = module.params["state"]
    status          = module.params["status"]
    applycfg        = module.params["applycfg"]

    has_changed = False

    try:
        centreon = Centreon(url, username, password)
    except Exception as e:
        module.fail_json(
            msg="Unable to connect to Centreon API: %s" % e.message
        )

    st, poller = centreon.pollers.get(instance)
    if not st and poller is None:
        module.fail_json(msg="Poller '%s' does not exists" % instance)
    elif not st:
        module.fail_json(msg="Unable to get poller list %s " % poller)

    data = list()

    host_state, host = centreon.hosts.get(name)

    if not host_state and state == "present":
        try:
            data.append("Add %s %s %s %s %s %s" %
                        (name, alias, ipaddr,  instance, hosttemplates, hostgroups))
            centreon.hosts.add(
                name,
                alias,
                ipaddr,
                instance,
                hosttemplates,
                hostgroups
            )
            # Apply the host templates for create associate services
            host_state, host = centreon.hosts.get(name)
            host.applytemplate()
            has_changed = True
            data.append("Add host: %s" % name)
        except Exception as e:
            module.fail_json(msg='Create: %s - %s' % (e.message, data), changed=has_changed)

    if not host_state:
        module.fail_json(msg="Unable to find host %s " % name, changed=has_changed)

    if state == "absent":
        del_state, del_res = centreon.hosts.delete(host)
        if del_state:
            has_changed = True
            if applycfg:
                poller.applycfg()
            module.exit_json(
                changed=has_changed, result="Host %s deleted" % name
            )
        else:
            module.fail_json(msg='State: %s' % del_res, changed=has_changed)

    if status == "disabled" and int(host.activate) == 1:
        d_state, d_res = host.disable()
        if d_state:
            has_changed = True
            data.append("Host disabled")
        else:
            module.fail_json(msg='Unable to disable host %s: %s' % (host.name, d_state), changed=has_changed)

    if status == "enabled" and int(host.activate) == 0:
        e_state, e_res = host.enable()
        if e_state:
            has_changed = True
            data.append("Host enabled")
        else:
            module.fail_json(msg='Unable to enable host %s: %s' % (host.name, d_state), changed=has_changed)

    if not host.address == ipaddr and ipaddr:
        s_state, s_res = host.setparam('address', ipaddr)
        if s_state:
            has_changed = True
            data.append(
                "Change ip addr: %s -> %s" % (host.address, ipaddr)
            )
        else:
            module.fail_json(msg='Unable to change ip add: %s' % s_res, changed=has_changed)

    if not host.alias == alias and alias:
        s_state, s_res = host.setparam('alias', alias)
        if s_state:
            has_changed = True
            data.append("Change alias: %s -> %s" % (host.alias, alias))
        else:
            module.fail_json(msg='Unable to change alias %s: %s' % (alias, s_res), changed=has_changed)

    #### HostGroup
    if hostgroups:
        hg_state, hg_list = host.gethostgroup()
        if hg_state:
            hostgroup_list = list()
            if hg_list is not None:
                for hg in hg_list.keys():
                    hostgroup_list.append(hg)
            del_hostgroup = list()
            add_hostgroup = list()
            for hgp in hostgroups:
                if hgp.get('name') in hostgroup_list and hgp.get('state') == 'absent':
                    del_hostgroup.append(hgp.get('name'))
                elif hgp.get('name') not in hostgroup_list and (hgp.get('state') == "present" or hgp.get('state') is None):
                    add_hostgroup.append(hgp.get('name'))

            if add_hostgroup:
                s, h = host.addhostgroup(add_hostgroup)
                if s:
                    has_changed = True
                    data.append("Add HostGroup: %s" % add_hostgroup)
                else:
                    module.fail_json(msg='Unable to add hostgroup: %s, %s' % (add_hostgroup, h), changed=has_changed)

            if del_hostgroup:
                s, h = host.deletehostgroup(del_hostgroup)
                if s:
                    has_changed = True
                    data.append("Del HostGroup: %s" % del_hostgroup)
                else:
                    module.fail_json(msg='Unable to def hostgroup: %s, %s' % (del_hostgroup, h), changed=has_changed)

    #### HostTemplates
    if hosttemplates:
        ht_state, ht_list = host.gettemplate()
        if ht_state:
            template_list = list()
            if ht_list is not None:
                for tpl in ht_list.keys():
                    template_list.append(tpl)
            del_host_template = list()
            add_host_template = list()
            for tmpl in hosttemplates:
                if tmpl.get('name') in template_list and tmpl.get('state') == "absent":
                    del_host_template.append(tmpl.get('name'))
                elif tmpl.get('name') not in template_list\
                        and (tmpl.get('state') == "present"
                        or tmpl.get('state') is None):
                    add_host_template.append(tmpl.get('name'))

            if add_host_template:
                s, h = host.addtemplate(add_host_template)
                if s:
                    host.applytemplate()
                    has_changed = True
                    data.append("Add HostTemplate: %s" % add_host_template)
                else:
                    module.fail_json(msg='Unable to add hostTemplate: %s' % add_host_template, changed=has_changed)

            if del_host_template:
                s, h = host.deletetemplate(del_host_template)
                if s:
                    host.applytemplate()
                    has_changed = True
                    data.append("Del HostTemplate: %s" % del_host_template)
                else:
                    module.fail_json(msg='Unable to del hostTemplate: %s' % del_host_template, changed=has_changed)

    #### Macros
    if macros:
        m_state, m_list = host.getmacro()
        for k in macros:
            if k.get('name').find("$_HOST") == 0:
                current_macro = m_list.get(k.get('name'))
            else:
                current_macro = m_list.get('$_HOST' + k.get('name').upper() + '$')
            if current_macro is None and (k.get('state') == "present" or k.get('state') is None):
                s, m = host.setmacro(
                    name=k.get('name'),
                    value=k.get('value'),
                    is_password=k.get('is_password'),
                    description=k.get('description'))
                if s:
                    has_changed = True
                    data.append("Add macros %s" % k.get('name').upper())
            elif current_macro is not None and k.get('state') == "absent":
                s, m = host.deletemacro(k.get('name'))
                if s:
                    has_changed = True
                    data.append("Delete macros %s" % k.get('name'))
            elif current_macro is not None and (k.get('state') == "absent" or k.get('state') is not None):
                if not current_macro.value == k.get('value')\
                        or not int(current_macro.is_password) == int(k.get('is_password', 0))\
                        or not current_macro.description == k.get('description', ''):
                    s, m = host.setmacro(
                        name=k.get('name'),
                        value=k.get('value'),
                        is_password=k.get('is_password'),
                        description=k.get('description'))
                    if s:
                        has_changed = True
                        data.append("Upgade macros %s" % k.get('name'))

    #### Params
    if params:
        _, _ = host.getparams()
        for k in params:
            if k.get('value') != host.params[k.get('name')]:
                s, h = host.setparam(k.get('name'), k.get('value'))
                if s:
                    has_changed = True
                else:
                    module.fail_json(msg='Unable to set param %s: %s' % (k.get('name'), h), changed=has_changed)

    if applycfg and has_changed:
        poller.applycfg()
    module.exit_json(changed=has_changed, msg=data)


if __name__ == '__main__':
    main()
