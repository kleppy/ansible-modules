#!/usr/bin/python
DOCUMENTATION = '''
---
module: tform
short_description: Wrapper around terraform command.
description:
    - Evaluates, destroys and applies terraform templates
author: - Jon Hursey (jonhursey@gmail.com)"
options:
    tfcommand:
        description:
          - (Required) terraform command to execute
        default: None
        choices: ['apply', 'destroy', 'plan']
    working_dir:
        description:
          - (Required) working directory of terraform files
    clean:
        description:
          - Remove existing state/backup files from working_dir
        default: False
notes:
    - Assumes you have ENV Vars already set for auth.
requirements:
  - "python >= 2.6"
  - "python-terraform >= 0.8.6"
examples:
  - ansible-playbook vcenter_builds.yml --extra-vars "tfcommand=apply, clean=1, working_dir=/usr/share/terraform/vcenter/"
  -
  connection: local
  tasks:
  - tform: working_dir=~/tform/server tfcommand=destroy
    environment:
      VSPHERE_USER: 'admin'
      VSPHERE_PASSWORD: 'f00f00'
'''

import os
import json
import logging
import re
try:
    from python_terraform import *
except ImportError:
    tf_found = False
else:
    tf_found = True


def runtf(tf, cmd):
    changes=True
    if cmd == "plan":
       return_code, stdout, stderr = tf.cmd(cmd,no_color=IsFlagged)
       if stderr and return_code == 1:
           changes = False
    else:
       return_code, stdout, stderr = tf.cmd(cmd,no_color=IsFlagged, force=True )
    return return_code, stdout, stderr, changes

def main():
    tf = Terraform()
    module = AnsibleModule(
        argument_spec = dict(
           working_dir = dict(required=True),
           tfcommand = dict(required=True,choices=['apply','destroy','plan']),
           clean = dict(required=False, choices=BOOLEANS, default=0)
        ),
        supports_check_mode = False,
    )

# Normalize
    working_dir = module.params['working_dir']
    tfcommand = module.params['tfcommand']

# Validate path
    if os.path.lexists(working_dir):
        tf = Terraform(working_dir)
    else:
        module.fail_json(msg="No TerraForm Templates found in %s " %working_dir)

# Clean up tfvars/backups
    if clean:
       for files in os.listdir(working_dir):
          if re.search(".*\.(tfstate)(\.tfstate.backup)?", files):
            os.remove(os.path.join(working_dir, files))


# Terraform command validate
    if tfcommand in ["plan", "destroy", "apply"]:
       ret, results, stderr, changes = runtf(tf,tfcommand)
       results = str(results).split('\n')[:-1]
       if ret == 1:
          module.exit_json(changed=False, ret_code=ret, plan_output=results, stderr=stderr)
       else:
          module.exit_json(changed=changes, ret_code=ret, plan_output=results, stderr=stderr)

from ansible.module_utils.basic import *
if __name__ == '__main__':
  main()
