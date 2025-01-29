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

def sent_message_to_sqs(queue_url, message_body, region_name='eu-central-1'):
    try:
        sqs_client = boto3.client('sqs', region_name=region_name)
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
        print("Message ID:", response['MessageId'])
    except Exception as e:
        print("Error sending message:", str(e))
