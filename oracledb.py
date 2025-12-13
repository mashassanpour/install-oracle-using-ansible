#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.module_utils.basic import AnsibleModule
import os

try:
    import oracledb
except ImportError:
    oracledb_exists = False
else:
    oracledb_exists = True

def checkdb_status():
    try:
        conn = oracledb.connect(mode=oracledb.SYSDBA)
        cursor = conn.cursor()

        # Run the query
        cursor.execute("SELECT STATUS FROM V$INSTANCE")

        # Fetch one row
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except oracledb.DatabaseError as db_exc:
        error, = db_exc.args
        if error.code == 1034:
            return 'DOWN'
        else:
            return "Database error: {}".format(error.message)
    else:
            return row[0]

def run():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=['check','stop','start']),
            start_options=dict(type='str', required=False, default='open', choices=['open','mount','nomount']),
            oracle_home=dict(type='str', required=False, default=os.environ.get('ORACLE_HOME'), aliases=['home']),
            oracle_sid=dict(type='str', required=False, default=os.environ.get('ORACLE_SID'), aliases=['sid'])
        )
    )
    state = module.params['state']
    start_options = module.params['start_options']
    
    oracle_home = module.params['oracle_home']
    if oracle_home is None and os.environ.get('ORACLE_HOME') is None:
        module.fail_json(msg="ORACLE_HOME is not set in neither environment nor parameters. please set it either way.")
    elif oracle_home is not None:
        os.environ['ORACLE_HOME'] = oracle_home
    
    oracle_sid = module.params['oracle_sid']
    if oracle_sid is None and os.environ.get('ORACLE_SID') is None:
        module.fail_json(msg="ORACLE_SID is not set in neither environment nor parameters. please set it either way.")
    elif oracle_sid is not None:
        os.environ['ORACLE_SID'] = oracle_sid

    result = dict(
        changed=False,
        state=state,
        db_state = None
    )

    if not oracledb_exists:
        msg = "The oracledb module is required. 'pip install oracledb' should do the trick."
        module.fail_json(msg=msg)

    oracledb.init_oracle_client()
    
    if state == 'check':
        result['db_state'] = checkdb_status()
        if result['db_state'] in ('OPEN', 'MOUNTED', 'NOMOUNT', 'DOWN'):
            module.exit_json(**result)
        else:
            module.fail_json(msg=result['db_state'], state=result['state'])

    elif state == 'stop':
        stopdb(module, result)
    elif state == 'start':
        startdb(module, result, start_options)

if __name__ == '__main__':
    run()