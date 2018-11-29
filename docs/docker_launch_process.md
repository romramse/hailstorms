




# Docker Launch Process

This file details how the docker file is used.




## Start a load test script

A load test script is a python file which contains the necessary tasks and also a configuration section
which details how a test should be run.

The Hailstorms docker file can do one of two things:

    * Parse the load test script and launch load test on slaves
    * Perform the load test as a slave




## A typical load test run

This is how a typical load test is initiated; and also what happens under the hood

* The load test is activated: 
    
        docker run -it romram/hailstorms start scripts/load_test_script.py
        
    The script is analyzed and the requested amount of load test machines are activated

