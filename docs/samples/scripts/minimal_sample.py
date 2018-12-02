from locust import task
from framework.core.hailstorm import Hailstorm, HailSet

"""
    This script file is an example of a minimal script file. 
    It is runnable if you start the feeder.py script first with the command: 
    
        $ make feeder
    
    The you can start the test with: 
    
        $ hailstorms/local -s docs/samples/scripts/minimal_sample.py
"""


class Hails(HailSet):
    """
    This is the class that hold all the load test tasks.
    In this sample there is only one task but you can make more very easily.
    """
    @task
    def ok(self):
        self.client.get('/world')


class Coldfront(Hailstorm):
    """
    This is the main class that contains the config dict with the default profile and
    all eventual other profiles you might want.
    Here we have two profiles defined.
    The default profile is always selected.
    On top of that you can select one or more profiles when starting the script:
    
        $ hailstorms/local -s scripts/minimal_sample.py -p additional_profile
    
    ...or:
    
        $ hailstorms/local -s scripts/minimal_sample.py -p additional_profile+very_long
    
    The order of your named profiles matter since only the arguments within a profile will
    override arguments with the same name in previous named profiles. I.e.
    
    Using the profile order above is not the same thing as -p very_long+additional_profile
    since the constant_minutes argument in the very_long profile will be overridden by the
    same argument in profile additional_profile and end up as 5 minutes. This since profile
    additional_profile is applied after the very_long profile.
    """
    config = {
        'default': {
            'host': 'http://localhost:3456',
            'rps': 10,
            'slaves': ['localhost']
        },
        'additional_profile': {
            'timeout_seconds': 10.0,
            'rampup_minutes': 5,
            'constant_minutes': 5
        },
        'very_long': {
            'constant_minutes': 20
        }
    }
    task_set = Hails

"""
This last bit is here so that you can run the script as is directly in your IDE or terminal:

    $ python3 scripts/minimal_sample.py
    
"""
if __name__ == '__main__':
    Hailstorm.test(Coldfront, 'default')
