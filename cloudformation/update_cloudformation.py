import time
import os

import boto3

REGION = os.getenv("CF_REGION", "eu-central-1")
ENVIRONMENT_CODE = os.getenv("CF_ENV_CODE")
APPLICATION = os.getenv("CF_APPLICATION")
AWS_PROFILE_NAME = os.getenv("CF_PROFILE_NAME")
WEB_APP_IMAGE = os.getenv("CF_WEB_APP_IMAGE")
CLOUDFORMATION_BUCKET = f"s3-{REGION}-{ENVIRONMENT_CODE}-job-sandbox-cf-templates"

assert ENVIRONMENT_CODE in ["test", "stg", "prod", "sandbox"]

if AWS_PROFILE_NAME is not None:
    boto3.setup_default_session(profile_name=AWS_PROFILE_NAME)
cloud_formation_client = boto3.client('cloudformation', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)

print(f"DEPLOYING TO {APPLICATION} {ENVIRONMENT_CODE} ENVIRONMENT IN {REGION} REGION")

APP_STACKNAME = f"{APPLICATION}-{ENVIRONMENT_CODE}-stack"
app_params = {"ProductName": APPLICATION,
              "EnvironmentCode": ENVIRONMENT_CODE,
              "WebAppImage": WEB_APP_IMAGE,
              "DiscordPublicKey": os.getenv("DISCORD_PUBLIC_KEY"),
              "DiscordBotToken": os.getenv("DISCORD_BOT_TOKEN"),
              "GeocodingApiKey": os.getenv("GEOCODING_API_KEY")}


def update_cloudformation(stack_file, stack_name, params):
    print(f"deploying {stack_name}")
    try:
        existing_stacks = cloud_formation_client.describe_stacks(StackName=stack_name)['Stacks'][0]['StackId']
    except Exception as e:
        print(f"stack {stack_name} was not found. creating new one")
        existing_stacks = []

    print("files uploaded to s3")
    s3_client.upload_file(stack_file,
                          CLOUDFORMATION_BUCKET,
                          stack_file)

    if existing_stacks:
        cloud_form_command = cloud_formation_client.update_stack
    else:
        cloud_form_command = cloud_formation_client.create_stack

    try:
        cloud_form_command(StackName=stack_name,
                           TemplateURL=f"https://{CLOUDFORMATION_BUCKET}.s3.{REGION}.amazonaws.com/{stack_file}",
                           Parameters=[{'ParameterKey': k, 'ParameterValue': v} for k, v in params.items()],
                           Capabilities=['CAPABILITY_AUTO_EXPAND', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM']
                           )
    except Exception as e:
        if "No updates are to be performed" in str(e):
            print(f"no updates to be performed on {stack_name}. Skipping...")
            return
        else:
            raise e

    print("waiting for logs")
    time.sleep(4)
    events_to_print = []
    last_event = None
    while cloud_formation_client.describe_stacks(StackName=stack_name)['Stacks'][0][
        'StackStatus'] in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                           'DELETE_IN_PROGRESS', "ROLLBACK_IN_PROGRESS"]:

        response = cloud_formation_client.describe_stack_events(StackName=stack_name)['StackEvents'][0:20]
        for r in response:
            if r['EventId'] != last_event:
                events_to_print.append(r['EventId'])
            else:
                break

        last_event = response[0]['EventId']
        for e in events_to_print:
            print(e)

        events_to_print = []
        time.sleep(3)

    status = cloud_formation_client.describe_stacks(StackName=stack_name)['Stacks'][0]['StackStatus']
    if status in ["CREATE_FAILED", "UPDATE_FAILED", "DELETE_FAILED", "ROLLBACK_FAILED", "REVIEW_IN_PROGRESS",
                  "ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"]:
        raise Exception(f"stack {stack_name} failed to deploy: {status}")
    else:
        print(f"stack {stack_name} deployed: {status}")


update_cloudformation("cloudformation/app_stack.yaml", APP_STACKNAME, app_params)
