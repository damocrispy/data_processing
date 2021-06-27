import json
import base64
import zlib

with open('function_input.json', 'r') as input_json:
    input_dict = json.load(input_json)
    
vehicles = {}

#   Loop through all records in input file.
for record in input_dict['records']:

    #   If we've never seen this vehicle...
    if record['vehicle_id'] not in vehicles:
        #   ...initialise it's payload list.
        vehicles[record['vehicle_id']] = []

    #   Decode payload from base 64 then decompress.
    payload = record['payload']
    pl_decoded = base64.b64decode(payload)
    pl_decomp = zlib.decompress(pl_decoded)

    #   Add the payload to the payload list.
    vehicles[record['vehicle_id']].append(pl_decomp)