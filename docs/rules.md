




# Rules on how to manage slaves, cores and clients

The sheer complexity of using multiple load test machines with several CPU cores utilizing a lot of threads (clients) is large.

This document shows how we have been thinking and why.




## The even spread of load during ramp up

We want the load test graph to show as strait line as possible during ramp up.
For this to happen we cannot start all slaves at the same time since then the ramp up phase would be jagged.

Therefor we try to control this by adding delays before activating a new slave and starting a new thread on that slave.

Example: We want to start 181 clients spread over two servers which has 7 CPU cores and we want all these clients started after three (3) minutes.

* The slaves, which we have little control over apart from at startup, we start as close to each other as possible.
    In this example that means that we start them one (1) second apart.

* The main locust process is started at each available CPU core. Normally this is all cores minus one.
  In this example we start these at a two (2) second interval.

* Each locust process has good control over the clients it starts so we leave the longest delay for this process to manage.
  In this example this is 14 seconds apart.
 
In total each slave is responsible for starting 90 clients.




## The chain of command

- docker run -it romram/hailstorms
    - entrypoint
        - start
            - verify_run_file
                - framework/core/hailstorm.py get_env_vars_string
                    - data.json
            - framework/scripts/start (expects data.json)
                - executes one locust per available core
            - exit 0
        - distribute
            - hailstorms/start
                - generate unique filename (must be moved up in chain)
                - framework/core/hailstorm.py get_env_vars_string
                    - data.json + env vars
                - clean up slaves dir
                - start docker on each slave via ssh access
