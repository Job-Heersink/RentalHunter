#!/bin/bash
set -e

REGION=eu-central-1
#export ENV_CODE=...
#export AWS_PROFILE=...
#AWS_ECR_REPO=...
IMAGE_NAME=woning-bot
APPLICATION_NAME=woning-bot
FUNCTION_NAME=lambda-$ENV_CODE-$APPLICATION_NAME-scraper
IMAGE_URI=$AWS_ECR_REPO/$IMAGE_NAME:latest

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ECR_REPO
docker build -t $IMAGE_NAME .
docker tag $IMAGE_NAME:latest $IMAGE_URI
docker push $IMAGE_URI

export CF_REGION=$REGION
export CF_ENV_CODE=$ENV_CODE
export CF_APPLICATION=$APPLICATION_NAME
export CF_WEB_APP_IMAGE=$IMAGE_URI
python3.9 cloudformation/update_cloudformation.py


UPDATE_RETURN=$(aws lambda update-function-code --function-name $FUNCTION_NAME --image-uri $IMAGE_URI --region $REGION)

STATUS='InProgress'
while [ "$STATUS" == "InProgress" ]
do
  sleep 3
  STATUS=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query "Configuration.LastUpdateStatus" --output text)
  echo $STATUS
done
echo "Update complete"