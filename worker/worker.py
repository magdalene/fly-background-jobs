import importlib
import json
import os
import redis

REDIS_TASK_INFO_KEY = os.environ.get("REDIS_TASK_INFO_KEY")
REDIS_RESULTS_KEY = os.environ.get("REDIS_RESULTS_KEY")

REDIS_URL = os.environ.get("REDIS_URL")

redis_client = redis.from_url(REDIS_URL)


def get_task_info():
    return json.loads(redis_client.get(REDIS_TASK_INFO_KEY))


def run_task(task_info):
    module_name = task_info["module"]
    fn_name = task_info["function_name"]
    args = task_info.get("args", [])
    kwargs = task_info.get("kwargs", {})
    module = importlib.import_module(module_name)
    task_fn = getattr(module, fn_name)
    status = "SUCCESS"
    try:
        result = task_fn(*args, **kwargs)
    except Exception as e:
        status = "FAILED"
        result = str(e)
    return {
        "status": status,
        "result": result
    }


def write_results(results):
    redis_client.set(REDIS_RESULTS_KEY, json.dumps(results))


def main():
    task_info = get_task_info()
    results = run_task(task_info)
    write_results(results)


if __name__ == '__main__':
    main()