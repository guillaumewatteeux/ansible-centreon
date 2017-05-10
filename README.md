## Ansible Centreon Module ##

IN DEVELOPMENT !!! Use as ours risks

### Install ###

Install required centreonapi (> 0.0.2) python library

Copy `library/centreon_host.py` on your Ansible


### Use It ! ###

Playbook example

```yaml
- hosts: all
  tasks:
    - name: Add host to Centreon platform
      centreon_host:
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
      delegate_to: localhost
```

### Default values ###

`instance` : Central
`status`: enabled
`state`: present