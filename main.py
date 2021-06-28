import json
import base64
import zlib
from itertools import groupby
from datetime import datetime as dt


def unpack(input_dict):

    vehicles = {}

    #   Loop through all records in input object.
    for record in input_dict['records']:

        #   If we've never seen this vehicle...
        if record['vehicle_id'] not in vehicles:
            #   ...initialise it's payload list.
            vehicles[record['vehicle_id']] = []

        #   Decode payload from base 64...
        payload = record['payload']
        pl_decoded = base64.b64decode(payload)
        #   ...then decompress...
        pl_decomp = zlib.decompress(pl_decoded)
        #   and then convert to dict.
        pl_dict = json.loads(pl_decomp)

        #   Add the payloads to the payload list.
        vehicles[record['vehicle_id']].extend(pl_dict['tracking'])

    return vehicles

def get_average_speed(vehicle):
    
    speeds = []
    #   Compile list of speeds.
    for datapoint in vehicle:
        speeds.append(datapoint['speed'])
    #   Retrun average speed.
    return sum(speeds)/len(speeds)

def get_highest_average_speed(vehicles):

    #   Get average speed of each vehicle and compile into a dict.
    average_speeds = {}
    for vehicle in vehicles:
        average_speeds[vehicle] = get_average_speed(vehicles[vehicle])

    #   Iterate through dict of average speeds and find largest.
    max_average = 0
    max_id = 0
    for id, speed in average_speeds.items():
        if speed > max_average:
            max_average = speed
            max_id = id

    return (max_id, max_average)

def get_statuses(vehicles):

    #   Iterate through vehicles.
    for vehicle in vehicles:

        #   For each of the vehicle's datapoints...
        for datapoint in vehicles[vehicle]:

            #   ...pull the ignition status and speed...
            ignition = datapoint['ignition']
            speed = datapoint['speed']

            #   ...and determine status.
            if ignition == 0 and speed == 0:
                datapoint['status'] = 'parked'
            elif ignition == 1 and speed == 0:
                datapoint['status'] = 'idling'
            elif ignition == 1 and speed > 0:
                datapoint['status'] = 'moving'

    return vehicles

def get_longest_streaks(vehicles):
    
    vehicle_streaks = []

    #   Iterate through vehicles.
    for vehicle in vehicles:

        status_streaks = {
            'parked': {
                'start': 'init',
                'longest': 0.0
            },
            'idling': {
                'start': 'init',
                'longest': 0.0
            },
            'moving': {
                'start': 'init',
                'longest': 0.0
            }
        }

        #   Loop through datapoints and pull out current and next statuses.
        for i in range(len(vehicles[vehicle]) - 1):
            current_status = vehicles[vehicle][i]['status']
            next_status = vehicles[vehicle][i+1]['status']

            #   If status doesn't change and this is the start of a new streak...
            if current_status == next_status and status_streaks[current_status]['start'] == 'init':
                #   ...save the timestamp as the streak start time.
                status_streaks[current_status]['start'] = vehicles[vehicle][i]['timestamp']

            #   If status changes...
            elif current_status != next_status:# and status_streaks[current_status]['start'] == 'init':
                #   ...calculate length of streak...
                last = dt.strptime(vehicles[vehicle][i+1]['timestamp'], "%Y-%m-%dT%H:%M:%S.000,+00:00")
                first = dt.strptime(status_streaks[current_status]['start'], "%Y-%m-%dT%H:%M:%S.000,+00:00")
                length = (last - first).total_seconds()
                #   ...and save it if its the longest.
                if length > status_streaks[current_status]['longest']:
                    status_streaks[current_status]['longest'] = length
                #   ...initialise the start time,...
                status_streaks[current_status]['start'] = 'init'

            #   If status doesn't change and this is an ongoing streak...
            elif current_status == next_status and status_streaks[current_status]['start'] != 'init':
                #   ...don't do anything.
                pass
        
        vehicle_streaks.append(status_streaks)

    return vehicle_streaks

def handler():

    #   Read contents of input file as a JSON object.
    with open('function_input.json', 'r') as input_json:
        input_dict = json.load(input_json)

    #   Convert to useable JSON object.
    vehicles = unpack(input_dict)

    #   Write results to a file.
    with open('function_ouput.json', 'w') as output_file:
        json.dump(vehicles, output_file, indent=4)

    print('There are ' + str(len(vehicles)) + ' vehicles in the dataset.')

    fastest_vehicle = get_highest_average_speed(vehicles)
    print('Vehicle with id ' + fastest_vehicle[0] + ' has highest average speed of ' + str(fastest_vehicle[1]))

    #   Augment the list of vehicles with parked/idling/moving status
    vehicles_statuses = get_statuses(vehicles)

    vehicles_streaks = get_longest_streaks(vehicles_statuses)
    print(vehicles_streaks)
    # get_longest_idling()
    # get_longest_moving()


    #   Write results to a file.
    with open('function_ouput.json', 'w') as output_file:
        json.dump(vehicles_streaks, output_file, indent=4)

    return

handler()