#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery.result import AsyncResult
from app.worker.celery_app import celery_app

def check_task_status(task_id):
    """Check the status and result of a Celery task"""
    result = AsyncResult(task_id, app=celery_app)
    
    print(f"Task ID: {task_id}")
    print(f"Status: {result.status}")
    print(f"Ready: {result.ready()}")
    print(f"Successful: {result.successful()}")
    print(f"Failed: {result.failed()}")
    
    if result.ready():
        if result.successful():
            print(f"Result: {result.result}")
        else:
            print(f"Error: {result.info}")
            if hasattr(result, 'traceback'):
                print(f"Traceback: {result.traceback}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        check_task_status(task_id)
    else:
        # Check the latest task we created
        check_task_status("8c1d702f-fde1-410a-8c0c-286ef4b8e4ee")