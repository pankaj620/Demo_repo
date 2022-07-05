import json
import boto3
import logging
import csv

logger = logging.getLogger()
logger.setLevel(logging.INFO)
dyyy=boto3.client('dynamodb')
s3client=boto3.client('s3')

def lambda_handler(event, context):
    roleName='crossaccount'
    list=[]
    logger.info("Main function started!!!")
    logger.info("Describing items of account_info table")
    try:
        logger.info("Scanned account info table")
        res=dyyy.scan(TableName='accnt_info',AttributesToGet=['account_id','region'],)
        logger.info("Fetching account Id and its region from the table")
        #print(res)
        lenn=len(res['Items'])
        for i in range(0,lenn):
            account_id=res['Items'][i]['account_id']['N']
            region=res['Items'][i]['region']['S']
            m=searching_regions(region,account_id)
            session=assume_role(account_id,roleName)
            for k in m:
                logger.info(f"Listing lambda functions for region {k} in the account {account_id}")
                lambd=session.client('lambda',region_name=k)
                #list.append(region)
                response=lambd.list_functions()
                length=len(response['Functions'])
                if length==0:
                    logger.info(f"Not any lambda function in the region {k} in the account {account_id}")
                else:
                    for j in range(0,length):
                        function_name=response['Functions'][j]['FunctionName']
                        print(function_name)
                        runtime=response['Functions'][j]['Runtime']
                        print(runtime)
                        
    except Exception as e:
        logger.info("Unbale to scan account info table")
    #with open('/tmp/function_details.csv', 'rb') as data:
        #s3client.put_object(Bucket='my-random-store',Key='function_details.csv',Body=data)


def assume_role(accountId, roleName):
    sts_client = boto3.client('sts')
    partition = sts_client.get_caller_identity()['Arn'].split(":")[1]
    response = sts_client.assume_role(
    RoleArn='arn:{}:iam::{}:role/{}'.format(
    partition, accountId, roleName),
    RoleSessionName='crossaccount'
    )
    sts_session = boto3.Session(
    aws_access_key_id=response['Credentials']['AccessKeyId'],
    aws_secret_access_key=response['Credentials']['SecretAccessKey'],
    aws_session_token=response['Credentials']['SessionToken']
    )
    logger.info("Assumed session for {}.".format(accountId))
    return sts_session


def searching_regions(region,account_id):
    l=[]
    flag=0
    regionlist={"in":["ap-south-1"],"us":['us-east-1','us-west-2'],"sgp":["ap-southeast-1","ap-northeast-1"],"eu":['eu-west-1',"eu-central-1"]}
    for i in regionlist:
        if region==i:
            flag=1
            l=regionlist[i]
            break
    if flag==1:
        logger.info(f"found the region for the account {account_id}")
    else:
        return
    return l
