## Ansible Centreon Module ##

IN DEVELOPMENT !!! Use as ours risks

### Install ###

Install required centreonapi (> 0.0.2) python library

Copy `library/centreon_*.py` on your Ansible `library` path


### Use It ! ###

Playbook example

```yaml
- hosts: localhost
  vars:
    centreon_url: "http://192.168.189.128/centreon"
    centreon_api_user: "admin"
    centreon_api_pass: "centreon"

  handlers:
    - name: "centreon api applycfg"
      centreon_poller:
        url: "{{ centreon_url }}"
        username: "{{ centreon_api_user }}"
        password: "{{ centreon_api_pass }}"
      listen: "centreon api applycfg"

  tasks:
    - name: Add host to Centreon
      centreon_host:
        url: "{{ centreon_url }}"
        username: "{{ centreon_api_user }}"
        password: "{{ centreon_api_pass }}"
        name: "{{ ansible_hostname }}"
        alias: "{{ ansible_fqdn }}"
        ipaddr: "{{ ansible_default_ipv4.address }}"
        hosttemplates:
          - OS-Linux-SNMP-custom
          - OS-Linux-SNMP-disk
        hostgroups:
          - Linux-Servers
          - Production-Servers
        instance: Central
        status: enabled
        state: present
        params:
          notes_url: "https://wiki.company.org/servers/{{ ansible_fqdn }}"
          notes: "My Best server"
        macros:
          MACRO1: value1
          MACRO2: value2
        applycfg: False
      delegate_to: localhost
      notify: "centreon api applycfg"

```

### Default values ###

 * `instance` : Central
 * `status`: enabled
 * `state`: present