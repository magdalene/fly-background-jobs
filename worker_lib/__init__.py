import json
import os
import uuid

import redis
import requests

FLY_API_TOKEN = os.environ.get("FLY_API_TOKEN")
FLY_API_HOST = os.environ.get("FLY_API_HOST", "api.machines.dev")

FLY_TASKS_APP = os.environ.get("FLY_TASKS_APP")
FLY_TASKS_ORG = os.environ.get("FLY_TASKS_ORG", "personal")
FLY_REGION = os.environ.get("FLY_REGION", "ams")

WORKER_IMAGE = os.environ.get("WORKER_IMAGE", "dshock/flyio-machines-worker:latest")
REDIS_URL = os.environ.get("REDIS_URL")

TASKS_KEY_PREFIX = "tasks:"
RESULTS_KEY_PREFIX = "results:"
MACHINE_INFO_KEY_PREFIX = "machines:"

headers = {
    "Authorization": f"Bearer {FLY_API_TOKEN}",
    "Content-Type": "application/json"
}


def _generate_task_id(function_name):
    return f"{function_name}-{uuid.uuid4()}"


def run_task(module_name, function_name, args=None, kwargs=None):
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    args = args or []
    kwargs = kwargs or {}
    task_id = _generate_task_id(function_name)
    redis_task_info_key = f"{TASKS_KEY_PREFIX}{task_id}"
    redis_results_key = f"{RESULTS_KEY_PREFIX}{task_id}"
    machine_config = {
        "name": task_id,
        "region": FLY_REGION,
        "config": {
            "image": WORKER_IMAGE,
            "env": {
                "REDIS_TASK_INFO_KEY": redis_task_info_key,
                "REDIS_RESULTS_KEY": redis_results_key
            },
            "processes": [{
                "name": "worker",
                "entrypoint": ["python"],
                "cmd": ["worker.py"]
            }]
        }
    }
    redis_client.set(redis_task_info_key, json.dumps({
        "module": module_name,
        "function_name": function_name,
        "kwargs": kwargs,
        "args": args
    }))
    response = requests.post(
        f"https://{FLY_API_HOST}/v1/apps/{FLY_TASKS_APP}/machines", headers=headers, json=machine_config
    )
    response.raise_for_status()

    # store the machine id so we can look it up later and see the status
    machine_id = response.json()["id"]
    redis_client.set(f"{MACHINE_INFO_KEY_PREFIX}{task_id}", machine_id)
    return {
        "task_id": task_id
    }


def get_results(task_id):
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    # check whether the machine is still running
    machine_id = redis_client.get(f"{MACHINE_INFO_KEY_PREFIX}{task_id}")
    response = requests.get(f"https://{FLY_API_HOST}/v1/apps/{FLY_TASKS_APP}/machines/{machine_id}", headers=headers)

    machine_info = response.json()
    if machine_info["state"] in ("starting", "created", "started"):
        return {
            "status": "PENDING"
        }

    result = redis_client.get(f"{RESULTS_KEY_PREFIX}{task_id}")
    if result is not None:
        return json.loads(result)

    return {
        "status": "FAILED",
        "result": f"Unknown failure; worker machine state {machine_info['state']}, but no result in Redis."
    }


def clean_up(task_id):
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    machine_id = redis_client.get(f"{MACHINE_INFO_KEY_PREFIX}{task_id}")
    requests.delete(f"https://{FLY_API_HOST}/v1/apps/{FLY_TASKS_APP}/machines/{machine_id}", headers=headers)
    redis_client.delete(f"{TASKS_KEY_PREFIX}{task_id}")
    redis_client.delete(f"{RESULTS_KEY_PREFIX}{task_id}")
    redis_client.delete(f"{MACHINE_INFO_KEY_PREFIX}{task_id}")