def getit(sRequest, eIndication, eStatus, eIndex, varBinds,info):
    
    print(info)
    for row in varBinds:
        if str(row[0][0]).startswith((CPU_Used)):
            data = map(str, (item for s in row for item in s))
            print (list(data))
def do_snmp( hostname):
        # pp.pprint( args )
        #stack_data = defaultdict(dict)
        outPut = ''
        # get snmp data
        cmdGen = cmdgen.AsynCommandGenerator()

        cmdGen.bulkCmd(
                cmdgen.CommunityData(passw),
                cmdgen.UdpTransportTarget((hostname, 161), retries=2),
                0, 20,
                #(Hostname, Model, Uptime, Location),
                (CPU_Used, CPU_Free, CPU_5Sec, CPU_1Min,CPU_5Min ),
                 (getit,('test'))        
        )
        


        cmdGen.snmpEngine.transportDispatcher.runDispatcher()
        
        #print(stack_data)

      
do_snmp(hostname)
