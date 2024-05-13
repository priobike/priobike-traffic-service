import base64
import socket
import os
import requests
import time
import random

def push_to_workers(file_path, file_content):
    worker_username = os.environ.get('WORKER_BASIC_AUTH_USER', None)
    worker_password = os.environ.get('WORKER_BASIC_AUTH_PASS', None)
    if worker_username is None or worker_password is None:
        raise Exception('WORKER_USERNAME or WORKER_PASSWORD not set')
    
    port = os.environ.get('WORKER_PORT', None)
    
    basic_auth = base64.b64encode(f'{worker_username}:{worker_password}'.encode()).decode()
    headers = {'Content-Type': 'application/json', 'Authorization': f'Basic {basic_auth}'}
    for worker_ip in get_worker_ips(port):
        url = f'http://{worker_ip}:{port}/upload/{file_path}'
        retries = 2
        success = False
        while retries > 0:
            response = requests.put(url, data=file_content, headers=headers)
            if response.status_code >= 200 and response.status_code < 300:
                success = True
                break
            print(f'Failed to push to worker {worker_ip}, response: {response.text}')
            print("Retrying...")
            random_wait_time = random.randint(1, 5)
            time.sleep(random_wait_time)
            retries -= 1
        if not success:
            raise Exception(f'Failed to push to worker {worker_ip}')
            
    
def get_worker_ips(port):
    host = os.environ.get('WORKER_HOST', None)
    if host is None or port is None:
        raise Exception('WORKER_HOST not set')
    worker_hosts = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    worker_ips = [worker_host[4][0] for worker_host in worker_hosts]
    return worker_ips