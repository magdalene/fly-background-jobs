## Demo of lightweight Python async worker library for web app with Fly Machines

Context: web applications often need to offload work to async workers (outside the http request lifecycle). There are a
number of common problems solved this way:

* Sending emails (which can be slow)
* Interacting with third-party APIs (also slow and sometimes unpredictable)
* Time/resource intensive image or text processing
* Generating artifacts (like reports, pdfs, etc.)
* Some data analysis tasks

One common way of solving this is a task queue (like Celery for Python or Sidekiq for Ruby). But running these require
configuring them, and using resources to run them. 

Alternative: a lightweight library built on top of Fly Machines using Redis for communicating back results. 

What it **won’t** do (that you might miss):

* All-in-one solution that also allows scheduling tasks (but some version of scheduling could be implemented by scheduling Machines)
* Plugins/apps that provide easy visibility into jobs (e.g., celery-flower gives a web UI for celery)
* ...surely many other features!

What it **will** do:

* Run expensive and/or time-consuming tasks in the background
* Communicate the results back when necessary
* Not require you to run any orchestrator or scheduler or queue software
* Not spend your money for workers when no work is being done (without any complicated scaling/orchestration)
* Retry tasks (right now this isn't configurable, but machines restart if they fail)

## What is in this repo

**NOT** a real production-ready library to do the above! This is a proof of concept. There are some ugly hacky things here.

### app.py

It's just a Flask app, with a form to send an email and see the results.

### worker

It's the worker implementation, including the task (which actually sends the email).

### worker_lib

This is the interesting(ish) part! This is the code that runs tasks using Fly Machines and retrieves results.

## How to get the demo running

### Build and push the worker image (optional)

You can skip this step and just use my image if you want.

```bash
cd worker
docker build -t dshock/flyio-machines-worker:latest . # change to your own image name
docker push dshock/flyio-machines-worker:latest
```

(TODO: probably we can build the worker image on fly instead.)

### Set worker app & redis on fly

Create the app for the machines that run tasks, and a Redis instance:
```bash
fly apps create my-machine-tasks # name your app something appropriate!
fly redis create
# take note of redis url! Or later use `fly redis status` to find it.
```

Create the secrets the tasks will need. That means `REDIS_URL`, and for the email sending
demo, Mailjet credentials:

```bash
fly secrets -a my-machine-tasks set REDIS_URL=<your redis url>
fly secrets -a my-machine-tasks set MAILJET_API_KEY=<your mailjet API key>
fly secrets -a my-machine-tasks set MAILJET_API_SECRET_KEY=<your mailjet API secret>
```

### Update fly.toml

You should update:

* env variable `FLY_TASKS_APP` to whatever app you created for the tasks (`my-machine-tasks` above).
* optionally, add an app name (if you don't, flyctl will ask you for it, that's fine too!)
* optionally, add a `WORKER_IMAGE` env variable with the image name you built above (if you don't, the default is my image)

### Set up and deploy the app!

First, create a fly.io access token ([link to manage API tokens](https://fly.io/user/personal_access_tokens)).
The app (worker_lib, in particular) needs this in order to manage machines that run tasks.

Then, set up the secrets for the Flask app:

```bash
fly secrets set REDIS_URL=<your redis url>
fly secrets set FLY_API_TOKEN=<your fly access token>
```

And last... deploy your app!

```bash
fly deploy
```

When this is complete, you can visit your app, and send an email!

Note: after you kick off the background task, you'll see that the status is "PENDING." Refresh
the page a few times, and it should get to "SENT."