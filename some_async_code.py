"""

Just a short example demonstrating a simple state machine in Python
This version is doing actual work, downloading the contents of
URL's it gets from a queue. It's also using gevent to get the
URL's in an asynchronous manner.
"""

import gevent
from gevent import monkey
monkey.patch_all()

import queue
import requests

job_Q = queue.Queue()

import time

class ET(object):
    def __init__(self):
        self.start_time = time.time()
    
    def __call__(self):
        return time.time() - self.start_time


def task(name, work_queue):
    while not work_queue.empty():
        url = work_queue.get()
        print(f'Task {name} getting URL: {url}')
        et = ET()
        a = requests.get(url)
        print(f'Task {name} got URL: {url}')
        job_Q.put_nowait(a.url)
        print(f'Task {name} total elapsed time: {et():.1f}')

def main():
    """
    This is the main entry point for the program
    """
    # create the queue of 'work'
    work_queue = queue.Queue()

    # put some 'work' in the queue
    for url in [
        "http://google.com",
        "http://yahoo.com",
        "http://linkedin.com",
        "http://shutterfly.com",
        "http://mypublisher.com",
        "http://facebook.com"
    ]:
        work_queue.put(url)

    # run the tasks
    et = ET()
    tasks = [
        gevent.spawn(task, 'One', work_queue),
        gevent.spawn(task, 'Two', work_queue),
        gevent.spawn(task, 'Three', work_queue),
        gevent.spawn(task, 'Four', work_queue),
        gevent.spawn(task, 'Five', work_queue)
    ]
    cc = gevent.joinall(tasks, timeout=1)
    print(cc)
    print(f'Total elapsed time: {et():.1f}')
    items = [job_Q.get() for _ in range(job_Q.qsize())]
    print(items)

if __name__ == '__main__':
    main()