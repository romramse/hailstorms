




# Welcome to your Hailstorms project

You have successfully initialized your project and gotten some help scripts in the same folder as this readme.

The help scripts are:

* __start__ - Use this if you want to run solely from your computer
* __inject__ - This script injects needed data into a remote linux machine and start the load on that machine

Both of these scripts has a usage feature that gives you instructions in the terminal. 
Simply call them without parameters like this:

    $ hailstorm/start
    
    $ hailstorm/inject




## Run locally

When running locally you in fact are running a docker container on your machine.
The advantage with this is apparent since you do not have to install the packages needed to run the load test.

##### Minimal test run

As a sample you have gotten a load test that goes towards google.
Please don't put a lot of load on that domain since it will only hurt yourself in extended delays or blacklisted ip address.
The base load of one request per second will suffice.

    $ hailstorm/start start --script scripts/google.py

This command will start up the docker container to execute the script scripts/google.py


