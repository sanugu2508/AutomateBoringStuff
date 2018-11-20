#from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902
#import pprint
from collections import defaultdict
import datetime
#from bnanode import bnanode
#import requests
#import requests.packages.urllib3
import binascii
from datetime import datetime, timedelta




#General Data
Hostname= '1.3.6.1.2.1.1.5'
Model = '1.3.6.1.2.1.47.1.1.1.1.2.1'
Uptime = '1.3.6.1.2.1.1.3'
Location = '1.3.6.1.2.1.1.6'


#Environmental Data

Env_Temp_Desc = '1.3.6.1.4.1.9.9.13.1.3.1.2' # Env Temperature Description
Env_Temp_Val = '1.3.6.1.4.1.9.9.13.1.3.1.3' # Env Temperature Value
Env_Fan_Desc = '1.3.6.1.4.1.9.9.13.1.4.1.2' # Fan Status
Env_Fan_Status = '1.3.6.1.4.1.9.9.13.1.4.1.3' # Fan Status 1-Normal, 2-Warning, 3-Critical, 4-Shutdown, 5-not present, 6-notfunctioning
Env_Power_Des = '1.3.6.1.4.1.9.9.13.1.5.1.2' # Env Power Supply
Env_Power_State = '1.3.6.1.4.1.9.9.13.1.5.1.3' # Env Power Supply 1-Normal, 2-Warning, 3-Critical, 4-Shutdown, 5-not present, 6-notfunctioning
Env_Power_Source = '1.3.6.1.4.1.9.9.13.1.5.1.4' # Env Power Supply source 1-unknown, 2-ac, 3-dc, 4-External Power Supply, 5-Internal Redundant

#Process Data
CPU_5Sec = '1.3.6.1.4.1.9.9.109.1.1.2.1.3'
CPU_1Min = '1.3.6.1.4.1.9.9.109.1.1.2.1.4'
CPU_5Min = '1.3.6.1.4.1.9.9.109.1.1.2.1.5'
CPU_Used = '1.3.6.1.4.1.9.9.109.1.1.1.1.12' # in kilo bytes
CPU_Free = '1.3.6.1.4.1.9.9.109.1.1.1.1.13' # in kilo bytes

#Stack Data
STACK_SWITCH_NUMBER = '1.3.6.1.4.1.9.9.500.1.2.1.1.1'
STACK_SWITCH_ROLE       = '1.3.6.1.4.1.9.9.500.1.2.1.1.3'
STACK_SWITCH_PRIORITY   = '1.3.6.1.4.1.9.9.500.1.2.1.1.4'

#HSRP Data
HSRP_VirtualIP = '1.3.6.1.4.1.9.9.106.1.2.1.1.11'
HSRP_Priority       = '1.3.6.1.4.1.9.9.106.1.2.1.1.3'
HSRP_Active   = '1.3.6.1.4.1.9.9.106.1.2.1.1.13'
HSRP_Standby   = '1.3.6.1.4.1.9.9.106.1.2.1.1.14'

#oid = input("Enter OID: ")
passw = 'N3tmGt5'
hostname = 's-upc-1.s03044.us'

def GetTime(sec):
    #sec = timedelta(seconds=int(input('Enter the number of seconds: ')))
    d = datetime(1,1,1) + timedelta(seconds=int(sec))

    #print("DAYS:HOURS:MIN:SEC")
    return ("%d days, %d hours, %d minutes, %d seconds" % (d.day-1, d.hour, d.minute, d.second))


def do_snmp( hostname):
        # pp.pprint( args )
        stack_data = defaultdict(dict)
        # get snmp data
        cmdGen = cmdgen.AsynCommandGenerator()

        cmdGen.bulkCmd(
                cmdgen.CommunityData(passw),
                cmdgen.UdpTransportTarget((hostname, 161), retries=2),
                0, 20,
                (Hostname, Model, Uptime, Location),
                (callbulk, ('GEN', hostname, stack_data)),                
        )
        
        cmdGen.bulkCmd(
                cmdgen.CommunityData(passw),
                cmdgen.UdpTransportTarget((hostname, 161), retries=2),
                0, 20,
                (CPU_Used, CPU_Free, CPU_5Sec, CPU_1Min, CPU_5Min),
                (callbulk, ('CPU', hostname, stack_data)),                
        )
        
        cmdGen.bulkCmd(
                cmdgen.CommunityData(passw),
                cmdgen.UdpTransportTarget((hostname, 161), retries=2),
                0, 20,
                (STACK_SWITCH_NUMBER, STACK_SWITCH_ROLE, STACK_SWITCH_PRIORITY),
                (callbulk, ('STACK', hostname, stack_data)),                
        )
        '''
        cmdGen.bulkCmd(
                cmdgen.CommunityData(passw),
                cmdgen.UdpTransportTarget((hostname, 161), retries=2),
                0, 20,
                (CPU_Used, CPU_Free, CPU_5Sec, CPU_1Min, CPU_5Min),
                (callbulk, ('HSRP', hostname, stack_data)),                
        )'''

        cmdGen.bulkCmd(
                cmdgen.CommunityData(passw),
                cmdgen.UdpTransportTarget((hostname, 161), retries=2),
                0, 20,
                (Env_Fan_Desc, Env_Fan_Status),
                #(Env_Temp_Desc, Env_Temp_Val, Env_Fan_Desc, Env_Fan_Status, Env_Power_Des, Env_Power_State, Env_Power_Source),
                (callbulk, ('ENV', hostname, stack_data)),                
        )

        cmdGen.snmpEngine.transportDispatcher.runDispatcher()
        
        print(stack_data)


def callbulk(sRequest, eIndication, eStatus, eIndex, varBinds, info):
        #print(type(varBinds[0][0]))
        
        #print(a)
        data_stack_role_dict = {
                '1': 'master',
                '2': 'member',
                '3': 'notMember',
                '4': 'standby'
        }
        
        key, hostname, stack_data = info
        #print( varBinds[0][1][1])
        '''
        for row in varBinds[0]:
                for row1 in row:
                        for row2 in row1:
                            print (row2)#a,b,c,d,e,f = row1
                            #print (row1)
        '''
              
        for row in varBinds:
                if key == 'GEN':
                        if str(row[0][0]).startswith((Hostname)):
                                _, hostname, _, model, _, uptime, _, location = map(str, (item for s in row for item in s))
                                #stack_data[hostname].setdefault(key, []).append((used, free, onesec, onemin, fivemin ))
                                print (50*'=')
                                print(20*' '+'General Data')
                                print (50*'=')
                                print("Hostname\t: %s" % hostname)
                                print("Uptime\t\t: %s" % GetTime(uptime))
                                print("Model\t\t: %s" % model)
                                print("Location\t: %s" % location)
                        else:
                                return False
                if key == 'CPU':
                        if str(row[0][0]).startswith((CPU_Used)):
                                _, cpuused, _, cpufree, _,cpuonesec, _, cpuonemin, _, cpufivemin = map(str, (item for s in row for item in s))
                                #stack_data[hostname].setdefault(key, []).append((used, free, onesec, onemin, fivemin ))
                                print (50*'=')
                                print(20*' '+'CPU Data')
                                print (50*'=')
                                print("CPU Usage\t: %d MB" % (int(cpuused)/1000))
                                print("CPU Free\t: %d MB" % (int(cpufree)/1000))
                                print("CPU One 1Sec\t: %s" % cpuonesec)
                                print("CPU One 1Min\t: %s" % cpuonemin)
                                print("CPU One 5Min\t: %s" % cpufivemin)
                                
                        else:
                                return False
                        
                if key == 'STACK':
                        data_stack_role_dict = {
                               '1': 'master',
                               '2': 'member',
                               '3': 'notMember',
                               '4': 'standby'
                        }
                        if str(row[0][0]).startswith((STACK_SWITCH_NUMBER)):
                                _, number, _, role, _, priority = map(str, (item for s in row for item in s))
                                #stack_data[hostname].setdefault(key, []).append((used, free, onesec, onemin, fivemin ))
                                print (50*'=')
                                print(20*' '+'Stack Data')
                                print (50*'=')
                                print("Stack Number\t: %s" % number)
                                print("Switch Role\t: %s" % data_stack_role_dict[role])
                                print("Priority\t: %s" % priority)
                                #print("Location\t: %s" % location)
                        else:
                                return False
                
                if key == 'ENV':
                        env_status_dict = {
                               '1': 'Normal',
                               '2': 'Warning',
                               '3': 'Critical',
                               '4': 'Shutdown' ,
                               '5': 'not present',
                               '6': 'notfunctioning'                             
                        }    
                        power_source_dict = {
                               '1': 'unknown',
                               '2': 'AC',
                               '3': 'DC',
                               '4': 'External Power Supply' ,
                               '5': 'Internal Redundant',
                                                         
                        }    

                        if str(row[0][0]).startswith((Env_Fan_Desc)):
                                _, tempdesc, _, tempval  = map(str, (item for s in row for item in s))
                                #_, tempdesc, _, tempval, _, fandesc, _, fanstat,  _, powerdesc, _, powerstat, _, powersrc  = map(str, (item for s in row for item in s))
                                stack_data[hostname].setdefault(key, []).append((tempdesc, tempval))
                                '''
                                print (50*'=')
                                print(20*' '+'ENV Data')
                                print (50*'=')
                                print("Temperate\t: %s , is %r" % (tempdesc, tempval))
                                #print("Fan Status\t: %s , is %r" % (fandesc, fanstat))
                                #print("Power\t\t: %s, %s, %s" % (powerdesc, powerstat, powersrc))
                                #print("Location\t: %s" % location)'''
                        else:
                                return False                            
            
        return True
        

      
do_snmp(hostname)      
