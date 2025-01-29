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
        print("Credențialele nu sunt configurate corect.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'UnauthorizedOperation':
            print(f"Eroare de autorizare: {e.response['Error']['Message']}")
        else:
            print(f"A aparut o eroare: {e}")
    except Exception as e:
        print(f"A aparut o eroare neasteptata: {e}")
    return None