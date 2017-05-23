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
    - name: Add Hostgroup
      centreon_hostgroup:
        url: "{{ centreon_url }}"
        username: "{{ centreon_api_user }}"
        password: "{{ centreon_api_pass }}"
        hg:
          - name: Linux-Server
            alias: Linux Server
          - name: ProjectA
            alias: Project AAAAAA ressources
          - name: MyHostgroup
       delegate_to: localhost
       run_once: true
  
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
          - name: notes_url
            value: "https://wiki.company.org/servers/{{ ansible_fqdn }}"
          - name: notes
            value: "My Best server"
        macros:
          - name: MACRO1
            value: value1
          - name: MACRO2
            value: value2
        applycfg: False
      delegate_to: localhost
      notify: "centreon api applycfg"

```

### Default values ###

 * `instance` : Central
 * `status`: enabled
 * `state`: present