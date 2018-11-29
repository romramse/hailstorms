#!/usr/bin/env python3
import math
import socket

import os

import boto3
import sys
import time


class AwsMetrics:

    def __init__(self, region='eu-west-2', metric_start_epoch='', metric_end_epoch=''):
        self.region = region
        self.metric_start_epoch = int(metric_start_epoch)
        self.metric_end_epoch = int(metric_end_epoch)
        self.test_time = self.metric_end_epoch - self.metric_start_epoch
        if self.test_time < 240:
            print("!! WARNING !! The test time was too short. ( < {} seconds )".format(240))
            exit(1)
        self.period = int(self.test_time / 60) * 60 - 180
        self.end_epoch = self.metric_end_epoch - 60
        self.start_epoch = self.end_epoch - self.period
        print('aws_metric_log="{}-{}={} {}-{}={}"'.format(
            self.metric_start_epoch, self.metric_end_epoch, self.test_time, self.start_epoch, self.end_epoch, self.period))

    def get_instances_by_name(self, name):
        print('aws_metric_service_name={}'.format(name))
        client = boto3.client('ec2', region_name=self.region)
        filters = [
            {
                'Name': 'tag:Name',
                'Values': [
                    name
                ]
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
        # print('Filters: {}'.format(filters))
        response = client.describe_instances(Filters=filters)
        # print('Response: {}'.format(response))
        result_instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                result_instances.append(instance['InstanceId'])
        print('aws_metric_no_instances={}'.format(len(result_instances)))
        return result_instances

    def get_load_balancer_by_member_instance_id(self, instance_id):
        client = boto3.client('elb', region_name=self.region)
        response = client.describe_load_balancers()
        for elb in response['LoadBalancerDescriptions']:
            name = elb['LoadBalancerName']
            # print(name)
            for instance in elb['Instances']:
                if instance['InstanceId'] == instance_id:
                    print('aws_metric_load_balancer_name={}'.format(elb['LoadBalancerName']))
                    return name
        print(response)

    def get_cloudwatch_metrics(self, namespace, metric_name, dimensions, statistics=['Average'], unit='Percent'):
        client = boto3.client('cloudwatch', region_name=self.region)
        response = client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=int(self.start_epoch),
            EndTime=int(self.end_epoch),
            Period=self.period,
            Statistics=statistics,
            Unit=unit
        )
        # print(response)
        response['period'] = self.period
        print('aws_metric_datapoints={}'.format(len(response['Datapoints'])))
        if len(response['Datapoints']) == 0:
            print('No datapoints has been retrieved for the given interval and service.')
            exit(1)
        return response

    def get_cpu_utilization(self, instances):
        # dimensions = [
        #     {
        #         'Name': 'InstanceId',
        #         'Value': instances[0]
        #     }
        # ]
        dimensions = []
        for instance_id in instances:
            if len(dimensions) > 9:
                break
            dimensions.append(
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                }
            )
        response = self.get_cloudwatch_metrics('AWS/EC2', 'CPUUtilization', dimensions, statistics=['Minimum','Maximum','Average', 'SampleCount', 'Sum'])
        cpu = response['Datapoints'][0]['Average']
        print('aws_metric_cpu_average={}'.format(cpu))
        print('aws_metric_datetime="{}"'.format(response['Datapoints'][0]['Timestamp']))
        return cpu

    def get_requests_per_second(self, load_balancer_name):
        dimensions = [
            {
                'Name': 'LoadBalancerName',
                'Value': load_balancer_name
            }
        ]
        response = self.get_cloudwatch_metrics('AWS/ELB', 'RequestCount', dimensions, statistics=['Minimum', 'Maximum', 'Average', 'SampleCount', 'Sum'], unit='Count')
        sum = response['Datapoints'][0]['Sum']
        period = response['period']
        rps = sum / period
        print('aws_metric_period={}'.format(period))
        print('aws_metric_count_average={}'.format(sum))
        print('aws_metric_rps_average={}'.format(rps))
        print('aws_metric_datetime="{}"'.format(response['Datapoints'][0]['Timestamp']))
        return rps

    def get_latency(self, load_balancer_name):
        dimensions = [
            {
                'Name': 'LoadBalancerName',
                'Value': load_balancer_name
            }
        ]
        response = self.get_cloudwatch_metrics('AWS/ELB', 'Latency', dimensions, statistics=['Minimum', 'Maximum', 'Average', 'SampleCount', 'Sum'], unit='Seconds')
        latency = response['Datapoints'][0]['Average']
        print('aws_metric_latency={}'.format(latency))
        return latency


def usage(argv):
    script_name = argv[0].rpartition('hailstorm/')[2]
    print('     usage: {} aws-service-name [start-epoch end-epoch] [period-lenght]'.format(script_name))
    print('         ')
    print('             aws-service-name    The name of the service that can be used to search for the service')
    print('                                 in the AWS console.')
    print('             start-epoch         A timestamp in epoch format (seconds) to mark the beginning of the metric.')
    print('             end-epoch           A timestamp in epoch format (seconds) to mark the end of the metric.')
    print('             period-length       The length, in seconds, of a period.')
    print('')
    print('             Please note that for this service to work the appropriate credentials has to be installed.')


if __name__ == '__main__':
    run_path = os.path.join(os.path.dirname(__file__), '../', '../')
    # print(time.time())
    if len(sys.argv) < 2 or sys.argv[1] == '':
        usage(sys.argv)
        exit(1)
    service_name = sys.argv[1].strip("'")
    start_time = ''
    end_time = ''
    if len(sys.argv) > 3:
        start_time = sys.argv[2]
        end_time = sys.argv[3]
    if len(sys.argv) > 4:
        period = sys.argv[4]
    aws = AwsMetrics('eu-west-2', start_time, end_time)
    instances = aws.get_instances_by_name(service_name)
    if len(instances) == 0:
        print('The service: "{}" does not have any running instances.'.format(service_name))
        exit(1)
    elb_name = aws.get_load_balancer_by_member_instance_id(instances[0])
    cpu = aws.get_cpu_utilization(instances)
    rps = aws.get_requests_per_second(elb_name)
    latency = aws.get_latency(elb_name)

