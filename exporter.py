import requests
import json
import uuid
import os
import time
import random

max_checkpoint = 200
headers = {'X-API-Key': 'default_secret'}
poll_empty_s = 1
poll_incomplete_s = 0.25
fail_cooldown_s = 10

class Exporter:
    def __init__(self, url):
        self.url = url

    """ Loads checkpoint from telemetry file """

    def load_checkpoint(self) -> int:

        if os.path.exists('exporter/checkpoint.txt'):
             # File exists: read it
            with open('exporter/checkpoint.txt', 'r') as f:
                    checkpoint = int(f.read().strip())
                    return checkpoint
        else:
            # File doesn't exist: create and write
            with open('exporter/checkpoint.txt', 'w') as f:
                f.write('0')
                checkpoint = 0
                return checkpoint
              
    """ Gets batch of max of 200 lines from telemetry file """

    def batch_getter(self) -> tuple:
        batch_id = str(uuid.uuid4())
        batch = []
        curr_checkpoint = self.load_checkpoint()

        with open('telemetry.jsonl', 'r') as f:
            f.seek(curr_checkpoint) # Jump to where we left off
            lines_read = 0

            # get new batch
            while lines_read < max_checkpoint:
                line = f.readline()
                if line == "":
                    status = 'batch_empty'
                    break
                elif line.endswith('\n'):
                    lines_read += 1
                    curr_checkpoint = f.tell()
                    batch.append(line)
                # read line and append to batch
                elif line != "" and not line.endswith('\n'):
                    status = 'batch_incomplete'
                    return batch, batch_id, curr_checkpoint, status
        
        if len(batch) == 0:
            status = 'batch_empty'
            return batch, batch_id, curr_checkpoint, status
        elif len(batch) != 0:
            status = 'batch_success'
            return batch, batch_id, curr_checkpoint, status
    
    """ Exports telemetry data to server by getting batch from batch getter """

    def exporter(self) -> tuple:
        # Get batch data from batch getter
        res = self.batch_getter()
        batch = res[0]
        batch_id = res[1]
        curr_checkpoint = res[2]
        status = res[3]

        # Check status if batch and return early if fail
        if status == 'batch_empty':
            return 'Nothing new to load, try again later', status
        if status =='batch_incomplete':
            return 'batch loaded incorrectly, please try again later', status
        
        filename = 'agent_id'  
        content_to_write = str(uuid.uuid4())
        
        if os.path.exists(filename):
        # File exists: read it
            with open(filename, 'r') as f:
                content = f.read()
                agent_id = content
        else:
            # File doesn't exist: create and write
            with open(filename, 'w') as f:
                f.write(content_to_write)
                agent_id = content_to_write

        body = {'batch_id': batch_id,
                'agent_id': agent_id,
                'lines': batch
                }
        
        retry_time = 0.25
        attempts = 1

        while attempts <= 6:
            try:
                response = requests.post(self.url, headers=headers, json=body, timeout=2.0)
        
                # Check status codes
                if response.status_code in [400, 401, 404]:
                    status = 'send_failed'
                    return 'Error occured, try again later', status
        
                # batch sent successfully
                elif response.status_code == 200:
                    with open('exporter/checkpoint.txt', 'w') as f:
                        f.write(str(curr_checkpoint))
                    status = 'send_success'
                    return curr_checkpoint, status
        
                # Timeout/server error occurred, trying again till 6 tries
                elif response.status_code == 429 or 500 <= response.status_code < 600:
                    attempts += 1
                    if attempts > 6:
                        break
                    sleep_s = min(retry_time, 5.0) * random.uniform(0.5, 1.5)
                    time.sleep(sleep_s)
                    retry_time *= 2
                    continue
        
                # Any other status code
                else:
                    status = 'send_failed'
                    return "Unexpected status code, try again later", status
    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                # Treat network errors like 429/5xx - retry with backoff
                attempts += 1
                if attempts > 6:
                    break
                sleep_s = min(retry_time, 5.0) * random.uniform(0.5, 1.5)
                time.sleep(sleep_s)
                retry_time *= 2
                continue
        status = 'send_failed'
        return "Batch can't be sent right now, please try again later", status
    
    """ Loop that runs until user interupts """
    def run_forever(self) -> None:

        print('Looping exporter, press C to stop.')
        while True:
            try:
                # Sleep based on what status we recieve from exporter or if use halts stop execution
                res = self.exporter()
                if res[1] == 'batch_empty':
                    time.sleep(poll_empty_s)
                    continue
                elif res[1] == 'batch_incomplete':
                    time.sleep(poll_incomplete_s)
                    continue
                elif res[1] == 'send_failed':
                    time.sleep(fail_cooldown_s)
                    continue
                elif res[1] == 'send_success':
                    time.sleep(0.1)
                    continue
            
            except KeyboardInterrupt:
                return
            
if __name__ == "__main__":
    # Replace with your actual server URL
    url = 'http://localhost:9000/ingest'
    exporter = Exporter(url)
    exporter.run_forever()