import time
import sys
import random
import json

levels = ['INFO', 'DEBUG', 'WARN', 'ERROR', 'CRITICAL']

while True:
    lvl = random.choice(levels)
    msg = json.dumps({
        'level': lvl, 
        'message': f'Simulasi log dengan level {lvl}', 
        'code': random.choice([200, 400, 500])
    })
    print(msg, flush=True)
    time.sleep(2)
