from datetime import datetime, timezone, timedelta

import boto3
import botocore
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
def get_instance_public_ip(instance_id, region='eu-central-1', public_ip=True):
    ec2 = boto3.client('ec2', region_name=region)
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running':
                    return instance['PublicIpAddress'] if public_ip else instance['PrivateIpAddress']
    except (NoCredentialsError, PartialCredentialsError):
        print("Credentialele nu sunt configurate corect.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'UnauthorizedOperation':
            print(f"Eroare de autorizare: {e.response['Error']['Message']}")
        else:
            print(f"A aparut o eroare: {e}")
    except Exception as e:
        print(f"A aparut o eroare neasteptata: {e}")
    return None

def get_instance_name(ec2, instance_id):
    response = ec2.describe_tags(
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [instance_id]
            },
            {
                'Name': 'key',
                'Values': ['Name']
            }
        ]
    )
    for tag in response['Tags']:
        if tag['Key'] == 'Name':
            return tag['Value']
    return "Unknown"
def get_cloudwatch_data(instance_id, region="eu-central-1"):
    session = boto3.Session(region_name=region)
    cloudwatch = session.client('cloudwatch')
    ec2 = session.client('ec2')

    all_metrics = []
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        instance_state = instance['State']['Name']
        instance_type = instance['InstanceType']
        public_ip = instance.get('PublicIpAddress', 'N/A')
        private_ip = instance.get('PrivateIpAddress', 'N/A')
        instance_name = get_instance_name(ec2, instance_id)
    except Exception as e:
        print(f"Error getting instance details for {instance_id}: {e}")
        return None

    metrics = ['CPUUtilization', 'NetworkIn', 'NetworkOut']

    for metric in metrics:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric,
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
            ],
            StartTime=datetime.now(timezone.utc) - timedelta(minutes=10),
            EndTime=datetime.now(timezone.utc),
            Period=300,
            Statistics=['Average']
        )
        for datapoint in response['Datapoints']:
            datapoint['Metric'] = metric
            datapoint['InstanceName'] = instance_name
            datapoint['InstanceState'] = instance_state
            datapoint['InstanceType'] = instance_type
            datapoint['PublicIP'] = public_ip
            datapoint['PrivateIP'] = private_ip
            if 'Timestamp' in datapoint:
                datapoint['Timestamp'] = datapoint['Timestamp'].isoformat()
            all_metrics.append(datapoint)

    return all_metrics
