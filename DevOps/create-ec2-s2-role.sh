#!/bin/bash
# ================================================
# create-ec2-s3-role.sh
# One-click IAM role: EC2 RunInstances + Full S3
# Run: ./create-ec2-s3-role.sh
# ================================================

set -e  # Exit on any error

# --- CONFIG: CHANGE THESE ---
ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID_HERE"
ROLE_NAME="Ec2S3CliRole"
PROFILE_NAME="ec2s3-role"
REGION="us-east-1"                         
# --------------------------------

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "Creating IAM role: $ROLE_NAME"

# 1. Create the role with trust policy
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --description "CLI role: launch EC2 instances + full S3 access" \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::'"${ACCOUNT_ID}"':root" },
      "Action": "sts:AssumeRole"
    }]
  }' > /dev/null

echo "Role created."

# 2. Attach AmazonS3FullAccess managed policy
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess > /dev/null

echo "Attached S3 full access policy."

# 3. Add inline policy for EC2 actions
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name Ec2RunInstancesPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ec2:RunInstances",
          "ec2:DescribeInstances",
          "ec2:DescribeImages",
          "ec2:DescribeInstanceTypes",
          "ec2:CreateTags",
          "ec2:CreateSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs"
        ],
        "Resource": "*"
      }
    ]
  }' > /dev/null

echo "Attached EC2 inline policy."

# 4. Add CLI profile to ~/.aws/config
CONFIG_FILE="$HOME/.aws/config"
mkdir -p "$(dirname "$CONFIG_FILE")"

# Remove old profile if exists
sed -i '' "/\[profile $PROFILE_NAME\]/,/^$/d" "$CONFIG_FILE" 2>/dev/null || true

# Append new profile
cat << EOF >> "$CONFIG_FILE"

[profile $PROFILE_NAME]
role_arn = $ROLE_ARN
source_profile = default
region = $REGION
EOF

echo "Added CLI profile: $PROFILE_NAME"
echo ""
echo "SUCCESS! Role created and CLI configured."
echo ""
echo "Use it like this:"
echo "  aws s3 ls --profile $PROFILE_NAME"
echo "  aws ec2 run-instances --image-id ami-0abcdef1234567890 --count 1 --instance-type t3.micro --profile $PROFILE_NAME"
echo ""
echo "Role ARN: $ROLE_ARN"
