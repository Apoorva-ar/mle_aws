terraform {
  backend "s3" {
    bucket         = "terraform-bucket-apoorva"
    key            = "terraform.tfstate"
    region         = "eu-west-3"  
  }
}

provider "aws" {
  region = "eu-west-3"
}

resource "aws_s3_bucket" "train_data_bucket" {
  bucket = "train-data-apoorva"
}

resource "aws_s3_bucket" "model_artifacts_bucket" {
  bucket = "model-artifacts-apoorva"
}

resource "aws_s3_bucket" "results_bucket" {
  bucket = "results-bucket-apoorva"
}

#following is not used but just for demonstration 
resource "aws_iam_role" "lambda_role" {
  name = "lambda-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "s3_access_policy" {
  name        = "s3_access_policy"
  description = "Allows read access to train and artifacts and write access to results bucket"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::train-data-apoorva/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::model-artifacts-apoorva/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::results-bucket-apoorva/*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_s3_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

resource "aws_lambda_function" "retraining_lambda" {
  function_name = "retraining-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "train.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  filename      = "train.zip"
  environment {
    variables = {
      DATA_STORE             = aws_s3_bucket.train_data_bucket.arn
      MODEL_ARTIFACTS_STORE  = aws_s3_bucket.model_artifacts_bucket.arn
    }
  }
}

