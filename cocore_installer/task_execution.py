import os
import requests
import asyncio
import subprocess
import tempfile
import json
import sys
import time
import traceback
from task_runners import TaskRunners
from task_extensions import TaskExtensions
MAX_THREADS = 10
AUTH_KEY = os.getenv("COCORE_AUTH_KEY")
LANGUAGE_MAP = {
    "1": "python",
    "2": "node",
    "3": "ruby",
    "4": "go",
    "5": "rust",
    "6": "java",
}

def run_task(task_language_id, task_requirements, task_code, input_args):
    task_language = LANGUAGE_MAP.get(str(task_language_id))
    if "python" in task_language:
        return TaskRunners.run_python_task(task_requirements, task_code, input_args, TaskExtensions.python_extension(input_args))
    elif "node" in task_language:
        return TaskRunners.run_node_task(task_requirements, task_code, input_args, TaskExtensions.node_extension(input_args))
    elif "ruby" in task_language:
        return TaskRunners.run_ruby_task(task_requirements, task_code, input_args, TaskExtensions.ruby_extension(input_args))
    elif "go" in task_language:
        return TaskRunners.run_go_task(task_requirements, task_code, input_args, TaskExtensions.go_extension(input_args))
    elif "rust" in task_language:
        return TaskRunners.run_rust_task(task_requirements, task_code, input_args, TaskExtensions.rust_extension(input_args))
    elif "java" in task_language:
        return TaskRunners.run_java_task(task_requirements, task_code, input_args, TaskExtensions.java_extension(input_args))
    else:
        return {"error": "UnsupportedLanguage", "error_message": f"Language '{task_language}' is not supported."}

async def process_task_execution(execution_id):
    try:
        task_execution = await fetch_task_execution(execution_id)
        task_language = task_execution['task']['language']
        task_code = task_execution['task']['code']
        task_requirements = task_execution['task']['requirements']
        input_args = task_execution['input'] or []

        result = run_task(task_language, task_requirements, task_code, input_args)

        result_url = f"https://cocore.io/task_executions/{execution_id}"
        headers = {
            "Authorization": f"Bearer {AUTH_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "task_execution": result
        }
        response = requests.patch(result_url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Task result posted successfully")
            return response.json()
        else:
            print(f"Failed to post task result: {response.status_code}")
            return {"error": f"Failed to post task result: {response.status_code}"}
    except Exception as e:
        print(f"Error processing task execution: {e}")
        print(traceback.format_exc())
        raise

async def fetch_task_execution(execution_id):
    try:
        url = f"https://cocore.io/task_executions/{execution_id}.json"
        headers = {
            "Authorization": f"Bearer {AUTH_KEY}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch task execution: {response.status_code}")
    except Exception as e:
        print(f"Error fetching task execution: {e}")
        print(traceback.format_exc())
        raise

async def process_task(input):
    """
    Execute the application code
    """
    await process_task_execution(input["input"].get("task_execution_id"))

def adjust_concurrency(current_concurrency):
    """
    Adjusts the concurrency level based on the current request rate.
    """
    return 10
