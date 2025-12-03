#!/bin/bash
# Initialize LocalStack AWS services for local development

echo "Initializing LocalStack..."

# Create SQS Queues
awslocal sqs create-queue --queue-name events-queue
awslocal sqs create-queue --queue-name delivery-queue
awslocal sqs create-queue --queue-name dead-letter-queue

# Set up DLQ redrive policy
awslocal sqs set-queue-attributes \
    --queue-url http://localhost:4566/000000000000/events-queue \
    --attributes '{
        "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:000000000000:dead-letter-queue\",\"maxReceiveCount\":5}"
    }'

awslocal sqs set-queue-attributes \
    --queue-url http://localhost:4566/000000000000/delivery-queue \
    --attributes '{
        "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:000000000000:dead-letter-queue\",\"maxReceiveCount\":5}"
    }'

# Create S3 bucket for event archival
awslocal s3 mb s3://triggers-api-archive

echo "LocalStack initialization complete!"
echo "Queues created:"
awslocal sqs list-queues
echo "Buckets created:"
awslocal s3 ls
