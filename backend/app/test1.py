import boto3

def lambda_handler(event, context):
    # EC2 client create చేయడం - మీ region ఇవ్వండి
    ec2 = boto3.client('ec2', region_name='eu-north-1')
    
    # మీ EC2 instance ID ఇవ్వండి
    instance_id = 'i-xxxxxxxxxxxxxxxxx'
    
    # Instance ని start చేయడం
    response = ec2.start_instances(InstanceIds=[instance_id])
    
    return {
        'statusCode': 200,
        'body': f'Instance {instance_id} start చేయబడింది'
    }