
chassis_900 = '192.168.65.30'

windows = 'localhost:4555'
chassis = '192.168.65.26:8022'

server_properties = {'windows': {'server': windows, 'locations': [f'{chassis_900}/1/1', f'{chassis_900}/1/2']},
                     'chassis': {'server': chassis, 'locations': [f'{chassis_900}/1/1', f'{chassis_900}/1/2']}}

# Default for options.
server = ['windows']
