# encoding: utf-8

from __future__ import with_statement
from threading import Thread, Condition
from collections import deque
import traceback

class ThreadPool(object):
    def __init__(self, workers=2):
        self.running = True
        self.work_available = Condition()
        self.queue = deque()
        self.threads = self._create_threads(workers)
    
    def execute(self, task):
        self.queue.append(task)
        with self.work_available:
            self.work_available.notify()
    
    def shutdown(self):
        self.running = False
        with self.work_available:
            self.work_available.notifyAll()
    
    def _create_threads(self, workers):
        def create_thread():
            thread = Thread(target=self._run)
            thread.start()
            return thread
        
        return [create_thread() for i in xrange(workers)]
    
    def _run(self):
        while self.running:
            task = None
            
            with self.work_available:
                try:
                    task = self.queue.popleft()
                except IndexError:
                    self.work_available.wait()
            
            if not task:
                continue
            
            try:
                task()
            except Exception:
                # don't let this thread die if the task throws an exception
                traceback.print_exc()
