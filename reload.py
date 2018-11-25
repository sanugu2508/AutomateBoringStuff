#!/usr/bin/python3

# get model
# get stack status
# reload
# get stack status
# compare

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902
import pprint
from collections import defaultdict
import datetime
from bnanode import bnanode
import requests
import requests.packages.urllib3

pp = pprint.PrettyPrinter( indent = 4 )
b = bnanode( user='xxxxx2', pw='Monday25')
b.login()

MODEL = '1.3.6.1.2.1.47.1.1.1.1.2.1'
STACK_SWITCH_NUMBER = '1.3.6.1.4.1.9.9.500.1.2.1.1.1'
STACK_SWITCH_ROLE       = '1.3.6.1.4.1.9.9.500.1.2.1.1.3'
STACK_SWITCH_PRIORITY   = '1.3.6.1.4.1.9.9.500.1.2.1.1.4'
passw = 'N3tmGt5'

BNASERVERS = [ 'bna-tst',
                                'bna-seg1.xxxxx.com',
                                'bna-seg2',
                                'bna-seg3',
                                'bna-seg4',
                                'bna-seg5',
                                'bna-seg6',
                                'bna-seg7' 
                                ]
SSL_VERIFY = False

def get_tokens():
        token_dict = dict()

        payload = {
                'grant_type': 'password',
                'username': 'xxxxx2',
                'password': 'Monday25'
        }

        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        for server in BNASERVERS:
                pp.pprint( 'Getting Token for: ' + server )
                r = requests.post( 'https://' + server + '/bca-networks/api/token', headers = headers, data = payload, verify=SSL_VERIFY 
)
                if r.status_code == 200:
                        token = r.json()
                        token = 'Bearer ' + token['access_token']
                        token_dict[server] = token
                else:
                        print( 'Unable to retrieve token from: ' + server )
        return token_dict
def get_node_id( hostname, token ):
        match = 0
        for server in BNASERVERS:
                # pp.pprint( server )
                headers = {'Accept': 'application/json', 'Authorization': token[server] }
                # pp.pprint( headers )
                url = 'https://' + server + '/bca-networks/api/v1.0/devices?filter.name=' + hostname + '.xxxxx.com'
                # pp.pprint( url )
                r = requests.get(url, headers = headers, verify = SSL_VERIFY )
                if r.status_code == 200:
                        data = r.json()
                        if len(data) == 1:
                                match = 1
                                return {'id': data[0]['id'], 'server': server}
                        elif len(data) > 1:
                                print( 'Too many matches for: ' + hostname)
                                return None
                        # return data[0]['id']
        if match == 0:
                print( hostname + ' not found on any bna server')
                return None


def do_stuff( args ):
        # pp.pprint( args )
        hostname, node_id, server, tokens = args
        stack_data = defaultdict(dict)
        # get snmp data
        cmdGen = cmdgen.AsynCommandGenerator()

        cmdGen.bulkCmd(
                cmdgen.CommunityData(passw),
                cmdgen.UdpTransportTarget((hostname, 161), retries=2),
                0, 20,
                (STACK_SWITCH_NUMBER, STACK_SWITCH_ROLE, STACK_SWITCH_PRIORITY),
                (callbulk, ('stack', hostname, stack_data)),
        )

        cmdGen.snmpEngine.transportDispatcher.runDispatcher()
        # validate we got a snapshot
        # pp.pprint( stack_data[hostname] )
        # generating a change ID

        if stack_data[hostname]:
                pp.pprint( 'Reloading ' + hostname)
                succ_flag = 0
                while succ_flag == 0:
                        job_id = stage_reload( node_id, server, tokens[server] )
                        if job_id:
                                if job_id == 999:
                                        # go get a new token
                                        print( hostname + ": bad token")
                                        tokens = get_tokens()
                                else: 
                                        print( hostname + ": Reload Staged"  )
                                        succ_flag = 1
                                        # execute the job
                        else:
                                print( hostname + ": Reload Failed")
                                succ_flag == 1
                        # kick the job off
                        pp.pprint( job_id )
                        job_status = execute_reload( server, tokens[server], job_id)
                        pp.pprint(job_status)
        else:
                pp.pprint( 'No pre-load data ' + hostname )
def execute_reload( server, token, job_id):
        headers = {'Content-type': 'application/json',
                                'Accept': 'text/plain',
                                'Authorization': token
                                }
        payload = {
                'jobIdOrKey': job_id
        }
        url = 'https://' + server + '/bca-networks/api/v1.0/jobs/' + job_id + '/submission'
        r = requests.post( url , headers = headers, json = payload, verify=SSL_VERIFY )
        pp.pprint( r.status_code )
        return r.status_code
def stage_reload( node_id, server, token ):
        headers = {'Content-type': 'application/json',
                                'Accept': 'text/plain',
                                'Authorization': token 
                                }
        change_id = '123456'

        payload = dict()
        payload.update({"changeID": change_id} )
        payload.update({"actions": [{
                                "@class":"com.bmc.bcan.rest.services.v1_0.JobService$SnapshotActionDTO",
                                "name": "Snapshot",
                                "spanParams":{
                                "spanIds": [
                                                node_id
                                        ] 
                                }
                        }]})

        url = 'https://' + server + '/bca-networks/api/v1.0/jobs'

        r = requests.post( url , headers = headers, json = payload, verify=SSL_VERIFY )
        if r.status_code == 201:
                loc = r.headers['location']
                blah = loc.split('/')
                job_id = blah[-1]
                pp.pprint( job_id )
                return ( job_id)
        elif r.status_code == 401:
                print( 'Bad Token')
                return( 999 )
        else:
                return( None )

        # v2_payload = {
        #         "changeID": "1234",
 #    "actions": [
 #      {
 #        "@class":"com.bmc.bcan.rest.services.v2_0.ActionService$SnapshotActionDTO",
 #        "actionNumber": 1,
 #        "name": "Snapshot",
 #        "spanParams":{
 #          "spanIds": [
 #              {
 #                "componentType": "Device",
 #                "id":"714294386-2050"
 #              }
 #            ]
 #        }
 #      }
 #    ]
        # }
        #r = requests.post( 'https://' + server + '/bca-networks/api/token', headers = headers, data = payload, verify=SSL_VERIFY )

def callbulk(sRequest, eIndication, eStatus, eIndex, varBinds, info):
        data_stack_role_dict = {
                '1': 'master',
                '2': 'member',
                '3': 'notMember',
                '4': 'standby'
        }

        key, hostname, stack_data = info
        for row in varBinds:
                if key == 'stack':
                        if str(row[0][0]).startswith((STACK_SWITCH_NUMBER)):
                                _, switch_num, _, role, _, priority = map(str, (item for s in row for item in s))
                                stack_data[hostname].setdefault(key, []).append((switch_num, data_stack_role_dict[role], priority))
                        else:
                                return False
        return True

#get devices
# devices = ['s-xxxxx-1.s00001.us', 's-xxxxx-2.s00001.us', 's-xxxxx-1.s00100.us', 's-xxxxx-2.s00100.us', 's-bak-1.s04712.us']
devices = ['s-xxxxx-1.s00001.us']
start = datetime.datetime.now()

# we need a token for each server
tokens = get_tokens()
# pp.pprint( tokens )
# get node_ids
device_dict = dict()
for hostname in devices:
        node_id = get_node_id( hostname, tokens )
        device_dict[hostname] = node_id

# pp.pprint( device_dict )
# for x in device_dict:
#       reload( x, device_dict[x]['token'], device_dict[x]['server'])

for x in device_dict:
        do_stuff( (x, device_dict[x]['id'], device_dict[x]['server'], tokens))
# with ProcessPoolExecutor(max_workers=10) as pool:
#       my_future = [pool.submit(do_stuff, (x, device_dict[x]['id'], device_dict[x]['server'], tokens)) for x in device_dict]
                #for future in as_completed(my_future):
                        #result = future.result()
                        #pp.pprint( result )

end = datetime.datetime.now() - start

# data = get_snmp_data('s-xxxxx-1.s00100.us')
# pp.pprint( data )
