# Ansible Centreon Module #

An Ansible module to configure Centreon

* HostGroup Management (add/del)
* Host Management (add, del, hosttemplate, hostgroup, macros, params, status)
* In development...

## Requirements ##

* Ansible >= 2.4.0 (ansible)
* centreonapi >= 0.1.3 

###Install ##

### Install CentreonAPI 

```shell
pip install centreonapi>=0.1.3
```

### Install Ansible-modules-centreon

```shell
$ cd YourPlayBookProject
$ cat >> galaxy_requirements.yml
- src: https://github.com/guillaumewatteeux/ansible-centreon.git
  scm: git
  version: dev
  name: ansible-modules-centreon

CTRL+D

$ ansible-galaxy install -r galaxy_requirements.yml
```

## Use It ! ##

Playbook example

```yaml
- hosts: server
  connection: local
  roles:
    - role: ansible-modules-centreon

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
          - name: OS-Linux-SNMP-custom
          - name: OS-Linux-SNMP-disk
          - name: OS-Linux-SNMP-dummy
            state: absent
        hostgroups:
          - name: Linux-Servers
          - name: Debian-Servers
            state: absent
          - name: ProjectA
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
            ispassword: 0
          - name: "$_HOSTMACRO2$"
            value: value2
            desc: macro description
            state: absent
        applycfg: False
      notify: "centreon api applycfg"

```

/!\ Warning about `params`: ansible module not idempotency with this options

## Default values ##

 * `instance` : Central
 * `status`: enabled
 * `state`: present
 
## AUTHOR INFORMATION

Guillaume Watteeux ([@guillaumewatteeux] (https://github.com/guillaumewatteeux))