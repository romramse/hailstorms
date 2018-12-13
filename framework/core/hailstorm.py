import json

import gevent
import random
import re
import string
import subprocess

import sys

import os

import ast

import time
from locust import HttpLocust, TaskSet, events, stats
from locust.clients import HttpSession


class CustomResponse(dict):

    def __init__(self, locust):
        super(CustomResponse, self).__init__()
        self.response = None
        self.delay = 0
        self.locust = locust


class HailSet(TaskSet):

    def wait(self):
        start = time.time()
        self._sleep(self.client.custom_response.delay)
        if self.client.locust.verbose > 0:
            print("Expected: {}  was: {}".format(self.client.custom_response.delay, time.time()-start))


class HailClient(HttpSession):
    __counter = 0
    __threads = 0
    __only_once_done = None
    __max_timeout = None
    natural_multiple = None

    def __init__(self, locust, *args, **kwargs):
        super(HailClient, self).__init__(locust.host, *args, **kwargs)
        HttpSession.CON_POOL_SIZE=300
        # print('Starting a client')
        self.locust = locust
        self.custom_response = CustomResponse(locust)

        if HailClient.__only_once_done is None:
            HailClient.__only_once_done = False
            self.__only_once()
            time.sleep(1)
            HailClient.__only_once_done = True
            # print('Client only once done!')
        else:
            wait_counter = 0
            while HailClient.__only_once_done is False or HailClient.__only_once_done is None:
                wait_counter += 1
                if wait_counter % 120 == 0:
                    print('Waiting for HailClient only once to finalize for too long (120 seconds). Killing job!')
                    exit(1)
                if wait_counter % 10 == 0:
                    print('.. client waiting..')
                time.sleep(1)

        self.server_index = os.getenv('hailstorm_server_index', 0)
        # print("server: {}".format(self.server_index))
        self.threads_used = os.getenv('hailstorm_threads_used', 0)
        self.id = HailClient.__counter * locust.run_config['id_multiple'] + locust.run_config['id_add'] + 1
        HailClient.__threads = int(HailClient.__counter * HailClient.natural_multiple + locust.run_config['id_add'] + 1)
        # print('Client {} with thread max {} using id-add:{}, m1:{} and m2:{}'. format(self.id, HailClient.__threads, locust.run_config['id_add'], locust.run_config['id_multiple'], HailClient.natural_multiple))
        HailClient.__counter += 1
        if HailClient.__max_timeout is None:
            HailClient.__max_timeout = locust.run_config['timeout_seconds']

    def __only_once(self):
        # print('Client only once')
        id_add = self.locust.run_config['id_add']
        HailClient.natural_multiple = 1
        try:
            HailClient.natural_multiple = (self.locust.run_config['clients'] - 1 - id_add) / \
                                          (self.locust.run_config['cores_clients'][id_add] - 1)
        except ZeroDivisionError:
            pass
        self.only_once()

    def only_once(self):
        """
        This method can be used to do something once per class instantiation to preserve memory and time.
        :return: Nothing
        """
        pass

    def head(self, url, assertion=None, **kwargs):
        return self.__do_request('HEAD', url, assertion, **kwargs)

    def get(self, url, assertion=None, **kwargs):
        return self.__do_request('GET', url, assertion, **kwargs)

    def put(self, url, assertion=None, **kwargs):
        return self.__do_request('PUT', url, assertion, **kwargs)

    def post(self, url, assertion=None, **kwargs):
        return self.__do_request('POST', url, assertion, **kwargs)

    def delete(self, url, assertion=None, **kwargs):
        return self.__do_request('DELETE', url, assertion, **kwargs)

    def options(self, url, assertion=None, **kwargs):
        return self.__do_request('OPTIONS', url, assertion, **kwargs)

    def __do_request(self, method, url, assertion, **kwargs):
        self.start_time = time.time()
        kwargs.setdefault('allow_redirects', True)
        kwargs.setdefault('timeout', HailClient.__max_timeout)
        kwargs.setdefault('catch_response', True)
        with self.request(method, url, **kwargs) as response:
            self.handle_response(response, assertion, **kwargs)
        return response

    def handle_response(self, response, assertion, **kwargs):
        self.custom_response.timestamp = int(time.time()*1000)
        self.custom_response.response = response
        self.custom_response.threads = HailClient.__threads
        self.custom_response.client_id = self.id
        self.custom_response.id_add = self.locust.run_config['id_add']
        meta = response.locust_request_meta
        self.custom_response.delay = self.locust.run_config['timeout_seconds'] - (meta['response_time'] / 1000.0) - 0.00200
        # self.custom_response.locust_expand_and_set_raw_response(response, self)
        self.execute_assertion_method(assertion, response, self.custom_response, **kwargs)
        # self.custom_response.update_from_response(response)
        self.locust.logger.log_custom_response(self.custom_response)
        self.locust.report(self.custom_response)

    def execute_assertion_method(self, assertion, response, custom_response, **kwargs):
        message = ''
        if assertion:
            try:
                result = assertion(response)
            except TypeError:
                result = assertion(response, custom_response)
            if type(result) == tuple:
                success, message = result
            else:
                success = result
            self.custom_response.assert_success = success
            self.custom_response.assert_message = message
            if not success:
                response.failure(message)


class Hailstorm(HttpLocust):
    config = {
        'base': {
            'verbose': 0,
            'host': 'http://localhost',
            'constant_minutes': 1.0,
            # comment
            'rampup_minutes': 1.0,
            # 'clients': 40,
            'rps': 10,
            'slaves': ['127.0.0.1']
        }

    }
    min_wait = 300
    max_wait = 300
    clients = 0
    run_path = None
    __only_once_done = None
    logger = None
    run_config = None

    def __init__(self):
        if Hailstorm.__only_once_done is None:
            Hailstorm.__only_once_done = False
            self.__only_once()
            self.run_config = Hailstorm.run_config
            self.only_once()
            time.sleep(0.1)
            Hailstorm.__only_once_done = True
            print('Hailstorm only once done!')
        else:
            wait_counter = 0
            while Hailstorm.__only_once_done is False:
                wait_counter += 1
                if wait_counter % 120 == 0:
                    print('Waiting for Hailstorm only once to finalize for too long (120 seconds). Killing job!')
                    exit(1)
                if wait_counter % 10 == 0:
                    print('.. hailstorm waiting {} seconds ..'.format(wait_counter))
                time.sleep(1)
            self.run_config = Hailstorm.run_config
        self.client = HailClient(self)
        self.logger = Hailstorm.logger
        self.verbose = self.run_config['verbose']
        # super(Hailstorm, self).__init__()

    def __only_once(self):
        print('Hailstorm only once!  ' + str(sys.argv))
        events.quitting += self.__only_once_at_the_end
        self.run_path = os.getcwd()
        profile = os.getenv('hailstorm_profile', 'default')
        id_add = os.getenv('hailstorm_id_add', 0)
        id_multiple = os.getenv('hailstorm_id_multiple', 1)
        server_index = os.getenv('hailstorm_server_index', 'missing')
        log_filename = os.getenv('hailstorm_log_filename', '000_test_logger')
        if server_index == 'missing':
            print('running locally')
            print('profile={}'.format(profile))
            Hailstorm.run_config = get_running_profile_from_config_dict(self.config, profile, '')
            Hailstorm.run_config = inspect_slaves(Hailstorm.run_config)
            Hailstorm.run_config = analyse_profile(Hailstorm.run_config)
        else:
            with open('/opt/hailstorms/running/data.json') as file_handle:
                Hailstorm.run_config = json.load(file_handle)
        Hailstorm.run_config['id_add'] = int(id_add)
        Hailstorm.run_config['id_multiple'] = int(id_multiple)
        Hailstorm.run_config['server_index'] = server_index

        Hailstorm.host = Hailstorm.run_config['host']
        Hailstorm.logger = CSVLogger(self.run_path + '/generated/' + log_filename)

    def __only_once_at_the_end(self, *args, **kwargs):
        self.only_once_at_the_end()

    def only_once(self):
        pass

    def only_once_at_the_end(self):
        pass

    def report(self, custom_response):
        pass

    @staticmethod
    def test(Hailstorm_class, profile='default', wait=-1000):
        try:
            run_path = os.getcwd()
            try:
                os.remove(run_path + '/generated/000_test_logger.csv')
            except OSError:
                pass
            events.request_success += Hailstorm.test_success
            events.request_failure += Hailstorm.test_failure
            os.environ['hailstorm_profile'] = profile
            hailstorm_instance = Hailstorm_class()
            hailstorm_instance.run_config['timeout_seconds'] = 1
            hailstorm_instance.run()
        except TypeError:
            print('task_set=None')
        except KeyboardInterrupt:
            pass

    @staticmethod
    def test_one_task(Hailstorm_class, task_name, profile='default'):
        # try:
        events.request_success += Hailstorm.test_success
        events.request_failure += Hailstorm.test_failure
        os.environ['hailstorm_profile'] = profile
        hailstorm_instance = Hailstorm_class()
        task_set = hailstorm_instance.task_set(hailstorm_instance)
        tasks = task_set.tasks
        for task in tasks:
            if task.__name__ == task_name:
                task(task_set)
                return
        task = tasks[0]
        print(task.__name__)
        #        except TypeError:
        #    print('task_set=None')


    @staticmethod
    def test_success(request_type, name, response_time, response_length):
        print('{:5} {:5d} bytes in {:5d} ms from {}'.format(request_type, response_length, response_time, name))
        print(str(stats.global_stats.num_requests))
        print(stats.global_stats.aggregated_stats().get_response_time_percentile(95))
        print(stats.print_stats(stats.global_stats.entries))

    @staticmethod
    def test_failure(request_type, name, response_time, exception):
        # print('\033[41;0;31m{:5} ERROR in {:5d} ms from {} - {}\033[0m'.format(request_type, response_time, name, exception))
        print('{:5} !! ERROR !! in {:5d} ms from {} - {}'.format(request_type, response_time, name, exception))
        print(str(stats.global_stats.num_requests))
        print(stats.global_stats.aggregated_stats().get_response_time_percentile(95))
        print(stats.print_stats(stats.global_stats.entries))


class CSVLogger(object):
    header_array = ['timeStamp', 'elapsed', 'label', 'responseCode', 'responseMessage', 'success',
                    'grpThreads', 'allThreads', 'Latency', 'load', 'p95', 'cid', 'of']

    def __init__(self, base_filename):
        super(CSVLogger, self).__init__()
        self.filename = base_filename + '.csv'
        try:
            os.makedirs(base_filename.rpartition('/')[0])
        except FileExistsError:
            pass    # That is fine
        if not os.path.isfile(self.filename):
            if not os.path.isfile(base_filename + '.lock'):
                with open(base_filename + '.lock', '+a') as lock_fh:
                    rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
                    lock_fh.write(rand_str + '\n')
                with open(base_filename + '.lock', 'r') as lock_fh:
                    read_str = lock_fh.readline().strip()
                    print("I'll write since {} == {}".format(read_str, rand_str))
                    print(' - The log filename is: {}'.format(self.filename))
                if read_str == rand_str and not os.path.isfile(self.filename):
                    open(self.filename, 'a').close()
                    self.log_row(','.join(CSVLogger.header_array))
                    time.sleep(1)
                    os.remove(base_filename + '.lock')

    def log_custom_response(self, custom_response):
        meta = custom_response.response.locust_request_meta
        success = 'false'
        try:
            if not custom_response.response.error:
                pass
        except AttributeError:
            success = 'true'
        status_message = str(custom_response.response.reason)
        if status_message == 'None':
            status_message = 'HTTP_FAILED'
        row_array = []
        row_array.append(str(custom_response.timestamp))
#        row_array.append(meta['elapsed'])
        row_array.append(str(meta['response_time']))
        row_array.append(meta['name'])
        row_array.append(str(custom_response.response.status_code))
        row_array.append(status_message)
        row_array.append(str(success))
        row_array.append(str(custom_response.threads))
        row_array.append(str(custom_response.threads))
        row_array.append(str(custom_response.response.elapsed.microseconds / 1000 + custom_response.response.elapsed.seconds * 1000))
        row_array.append(str(custom_response.delay))
        row_array.append(str(custom_response.locust.client.natural_multiple))
        row_array.append(str(custom_response.client_id))
        row_array.append('{}:{}:{}'.format(
            str(custom_response.locust.run_config['id_add']),
            str(custom_response.locust.run_config['server_index']),
            str(custom_response.locust.run_config['id_multiple'])
        ))
        self.log_row(','.join(row_array))

    def log_row(self, row):
        with open(self.filename, 'a') as file_handle:
            file_handle.write(row)
            file_handle.write('\n')
            file_handle.flush()


def get_config_dict_from_file(filename, log_filename):
    config_as_string = ''
    ignore = True
    curly_count = -1
    with open(filename) as fh:
        lines = fh.readlines()
        for line in lines:
            if ignore:
                if re.match('^ +config *= *\{', line):
                    curly_count = 0
                    ignore = False
            if not ignore:
                if re.match('.*\{.*', line):
                    curly_count += 1
                config_as_string += line
                if re.match('.*\}.*', line):
                    curly_count -= 1
            if curly_count == 0:
                break
    _first_curly_pos = config_as_string.index('{')
    _config = ast.literal_eval(config_as_string[_first_curly_pos:])
    try:
        test = _config['default']['rps']
    except KeyError:
        print("The config file lacks a default section")
        exit(1)
    _config['default']['script_filename'] = filename
    _config['default']['log_filename'] = log_filename
    return _config


def get_running_profile_from_config_dict(_config, profile_string, params_string):
    _running_profile = Hailstorm.config['base'].copy()
    if len(profile_string) == 0:
        profile_string = 'default'
    if 'default' not in profile_string:
        profile_string = 'default+' + profile_string
    _running_profile['profile'] = profile_string
    for _profile in profile_string.split('+'):
        try:
            temp_profile = _config[_profile]
            for key in temp_profile.keys():
                _running_profile[key] = temp_profile[key]
        except KeyError:
            print("The profile {} is missing".format(_profile))
            exit(1)
    _running_profile['params'] = params_string
    for _param_key_value in params_string.split(','):
        _key_value_array = _param_key_value.split('=')
        if len(_key_value_array) == 2:
            key = _key_value_array[0]
            value = _key_value_array[1]
            if len(value) > 0 and value[0] == '[':
                _running_profile[key] = value[1:-1].split()
            else:
                if key not in _running_profile.keys():
                    try:
                        if '.' in value:
                            _running_profile[key] = float(value)
                        else:
                            _running_profile[key] = int(value)
                    except ValueError:
                        _running_profile[key] = str(value)
                elif type(_running_profile[key]) is int:
                    _running_profile[key] = int(value)
                elif type(_running_profile[key]) is float:
                    _running_profile[key] = float(value)
                else:
                    _running_profile[key] = value
    return _running_profile


def decorate_running_profile(_running_profile):
    for key in _running_profile.keys():
        value = float(_running_profile[key])
        if key == 'clients':
            _running_profile['client_gap_seconds'] = _running_profile['rampup_minutes'] * 60.0 / value


def inspect_slaves(_running_profile):
    slave_cores = []
    total_cores = 0
    # TODO: Decide upon way to solve
    try:
        for slave in _running_profile['slaves']:
            if not slave in ['127.0.0.1', 'localhost']:
                result = subprocess.check_output(['/usr/bin/ssh', slave.strip("'"), 'nproc'])
            else:
                result = subprocess.check_output(['nproc'])
            cores = int(result)
            if cores > 1:
                cores -= 1
            slave_cores.append(cores)
            total_cores += int(cores)
        _running_profile['slaves_cores'] = slave_cores
        _running_profile['cores'] = total_cores
        return _running_profile
    except KeyError:
        print('Running profile doesn\'t have a slaves entry. ')


def analyse_profile(_running_profile):
    rps = int(_running_profile['rps'])
    try:
        clients = int(_running_profile['clients'])
        print('!! WARNING !! The clients value is set! Timeout_seconds value is recalculated. Clients value should only be used when important.')
        _running_profile.pop('timeout_seconds', None)
    except KeyError:
        try:
            timeout_seconds = int(_running_profile['timeout_seconds'])
            clients = rps * timeout_seconds
        except KeyError:
            print('!! WARNING !! Neither clients nor timeout_seconds has been set. Defaults to clients = rps and timeout_seconds = 1.')
            clients = rps
        _running_profile['clients'] = clients
    cores = int(_running_profile['cores'])
    rampup_seconds = float(_running_profile['rampup_minutes']) * 60
    constant_seconds = float(_running_profile['constant_minutes']) * 60
    rampup_ms = rampup_seconds * 1000

    total_requests = rps * (rampup_seconds/2 + constant_seconds)
    _running_profile['total_requests'] = total_requests
    _running_profile['constant_requests'] = rps * constant_seconds
    _running_profile['total_seconds'] = int(rampup_seconds * 2.0 + constant_seconds)
    _running_profile['rampup_seconds'] = int(rampup_seconds)
    _running_profile['constant_seconds'] = int(constant_seconds)

    if 'timeout_seconds' not in _running_profile:
        timeout_seconds = float(clients) / float(rps)
        if timeout_seconds > 10:
            print('!! WARNING !! The request timeout is larger that 10 seconds. Might lead to unstable load.')
        if timeout_seconds < 0.1:
            print('!! ERROR !! The request timeout seconds are less than 0.1 seconds.')
            exit(1)
        _running_profile['timeout_seconds'] = timeout_seconds

    clients_per_core = int(int(clients) / int(cores))
    clients_per_core_overflow = int(clients) - clients_per_core * int(cores)
    _running_profile['clients_per_core'] = clients_per_core
    _running_profile['clients_per_core_overflow'] = clients_per_core_overflow

    no_slaves = len(_running_profile['slaves_cores'])
    slave_delay_ms = rampup_ms / (clients)
    core_delay_ms = slave_delay_ms * no_slaves
    client_delay_ms = core_delay_ms * (cores / no_slaves)
    cores_clients = []
    cores_client_delay_ms = []
    for this_cores in _running_profile['slaves_cores']:
        for core_idx in range(0, this_cores):
            this_clients = clients_per_core
            if clients_per_core_overflow > 0:
                clients_per_core_overflow -= 1
                this_clients += 1
            cores_clients.append(this_clients)
            cores_client_delay_ms.append(slave_delay_ms * no_slaves * this_clients)
    _running_profile['cores_clients'] = cores_clients
    _running_profile['cores_client_delay_ms'] = cores_client_delay_ms
    _running_profile['slave_delay_seconds'] = slave_delay_ms / 1000.0
    _running_profile['core_delay_seconds'] = core_delay_ms / 1000.0
    _running_profile['client_delay_seconds'] = client_delay_ms / 1000.0
    return _running_profile


def update_from_environment(_running_profile):
    for key, value in os.environ.items():
        if key.startswith('hailstorm_'):
            _running_profile[key.rpartition('hailstorm_')[2]] = value


def get_env_vars_from_running_profile(_running_profile):
    _env_vars_string = ''
    for key in _running_profile.keys():
        value = _running_profile[key]
        if type(value) is list:
            _env_vars_string += 'hailstorm_{}=({})\n'.format(key, ' '.join("'" + str(val) + "'" for val in value))
        else:
            _env_vars_string += 'hailstorm_{}={}\n'.format(key, str(_running_profile[key]))
    if output_file != '':
        with open(output_file+'.env', 'w') as file_handle:
            file_handle.write(_env_vars_string)
    return _env_vars_string


def save_profile_as_json(_running_profile):
    if output_file != '':
        with open(output_file+'.json', 'w') as file_handle:
            file_handle.write(json.dumps(_running_profile, indent=2, sort_keys=True))


def usage():
    print("usage: hailstorm.py verb -s|--script script_filename [options]")
    print("       verbs:")
    print("                         get_config_dict_from_file   Scanning file for config dict and returns that.")
    print("                         get_running_profile         Calls get_config_dict_from_file and picks parameters")
    print("                                                     according to selected profile.")
    print("                         get_env_vars_string         Calls get_running_profile and makes env string ")
    print("                                                     from the parameters.")
    print("       options:")
    print("                         -p|--profile                profile to be used.")
    print("                         --params                    additional params to be overridden.")
    print("                         -o|--output_file            Base name of result files. (without extension)")
    print("")
    print("       script:           The script file is mandatory. Here is a minimal version of it:")
    print("                         ")
    print("                         from locust import task")
    print("                         from framework.core.hailstorm import Hailstorm, HailSet")
    print("                         ")
    print("                         ")
    print("                         class Hails(HailSet):")
    print("                         ")
    print("                             @task")
    print("                             def ok(self):")
    print("                                 self.client.get('/world')")
    print("                         ")
    print("                         ")
    print("                         class Coldfront(Hailstorm):")
    print("                             config = {")
    print("                                 'default': {")
    print("                                     'host': 'http://localhost:3456',")
    print("                                     'rps': 10,")
    print("                                     'slaves': [")
    print("                                         'micke@localhost'")
    print("                                     ]")
    print("                                 },")
    print("                                 'additional_profile': {")
    print("                                     'timeout_seconds': 10.0,")
    print("                                     'clients': 100,")
    print("                                     'rampup_minutes': 5,")
    print("                                     'constant_minutes': 5")
    print("                                 }")
    print("                             }")
    print("                             task_set = Hails")
    print("                         ")
    print("                         if __name__ == '__main__':")
    print("                             Hailstorm.test(Coldfront, 'default')")
    print("                         ")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        usage()
        exit(1)
    verb = sys.argv[1]
    script = ''
    profile = ''
    params = ''
    output_file = ''
    log_file = ''
    while len(sys.argv) > 2:
        switch = sys.argv.pop(2)
        if switch in ['-s', '--script']:
            script = sys.argv.pop(2)
        if switch in ['-p', '--profile']:
            profile = sys.argv.pop(2)
        if switch in ['--params']:
            params = sys.argv.pop(2)
        if switch in ['-o', '--output_file']:
            output_file = sys.argv.pop(2)
        if switch in ['--log_filename']:
            log_file = sys.argv.pop(2)
    if script == '':
        usage()
        exit(1)
    if verb == 'get_config_dict_from_file':
        config = get_config_dict_from_file(script, log_file)
        print(config)
    if verb == 'get_running_profile':
        config = get_config_dict_from_file(script, log_file)
        running_profile = get_running_profile_from_config_dict(config, profile, params)
        print(running_profile)
    if verb == 'get_env_vars_string':
        print('profile: {}, params: {}'.format(profile, params))
        config = get_config_dict_from_file(script, log_file)
        running_profile = get_running_profile_from_config_dict(config, profile, params)
        inspect_slaves(running_profile)
        analyse_profile(running_profile)
        update_from_environment(running_profile)
        save_profile_as_json(running_profile)
        env_vars_string = get_env_vars_from_running_profile(running_profile)
        print(env_vars_string)

