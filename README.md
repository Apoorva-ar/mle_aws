# End-to-End ML Project with CI/CD on AWS

This project aims to create a scalable machine learning infrastructure on AWS with continuous integration and deployment (CI/CD) in place. As an ML engineer, my goal is to build a scalable infrastructure that handles data processing, model retraining, and inference efficiently.

## Project Workflow
Tech stack: <br>
Docker, Flask, Terraform, Ansible, AWS, GitHub Actions
## Infrastructure Update using Terraform 
The infrastructure for this project is managed using Terraform. Terraform configuration file ``main.tf``. defines the required AWS resources, such as S3 buckets and necessary permissions. Use the following commands to set-up infra:<br>
Initialse the state<br>
```
terraform init
```
Create a plan and store in 'my_plan'
```
terraform plan -out my_plan
```
Apply the plan to create resources<br>
```
terraform apply my_plan
```

In order to destroy the infra, use <br>
```
terraform destroy
```
N.B Make sure the buckets are empty before you destroy infra conatining s3 buckets.<br>
Use `src/cleanup.py` to empty the buckets<br>
```
python cleanup.py
```
N.B Make sure AWS keys are configured with your code env/editor to be able to interact with AWS<br>

## Training/Retraining
Model retraining is triggerred by running train.py<br>
```
python train.py
```
It picks latest data from S3 bucket ``train-data`` and stores model artifacts such as model object, scaler object
and some metadata in the S3 bucket-``model-artifacts``. <br>
N.B Make sure there is some data in the ``train-data`` bucket before running train.py. This can be acheived using<br>
```
ansible-playbook upload_data.yml
```
This uploads a local csv file to S3 bucket

Alternately, model artifacts are zipped and can later be uploaded to the s3 bucket ``model-artifacts`` using <br>
```
ansible-playbook upload_model_af.yml
```
N.B. set up .env with following variables:
```
MODEL_ARTIFACTS_STORE=<name>
DATA_STORE=<name>
RESULTS_STORE=<name>
AWS_ACCESS_KEY=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-acess-key>
```

#### Future:
The retraining process will be triggered based on the event:<br>
- Data arrival: Whenever new data is put into the S3 bucket ``train-data``, it triggers the retraining process to incorporate the latest data.<br>
- Code change: When there is a merge to the main branch of code repository, initiate the retraining process to reflect any code updates.<br>

## Inference
- In the current implemetation the inference function ``predict.py`` runs as a Flask App in a docker container.<br>
- It is exposed to an end point that can receive POST requests with test data and model version in the body of the request.<br>
- The model corresponding to the model version passed is fetched from s3 bucket ``model-artifacts`` along with scaler object (same version) for pre-processing the test data.<br>
- The processed data is then scored by the model to generate predictions.<br>
- The prediction along with timestamp and test data are then put as csv in s3 bucket ``results-bucket``. If the file for the given version exists, the data is appended else a new file is created for that version.<br>
  
#### Start Flask App 
Build the docker image<br>
```
docker build -t image_name . 
```
Run the image attaching the port where you want to run your flask app and giving the environment file.<br>
The .env file contains the s3 bucket name and the AWS access and secret keys.<br>
N.B. The best practice is to store the keys in AWS Secrets Manager, but for now I will pass them as env variables stored in ``.env``<br>
```
docker run -p 8000:8000 --name my-container --env-file .env image_name
```
This will start the flask app at localhost port 8000 <br>

#### Test the app by sending in data
Navigate to folder tests and run <br>
```
python test_inference.py
```
This sends a POST request to the end point "http://localhost:8000/inference" with request body
```
{
    "data": [["aa", 2, 2]],
    "model_version": "1"
}
```
You will get response 'inference completed'<br>
The results will be added to the S3 bucket: ``results-bucket``. 

#### Future:
As a extension, the docker image can bet put in the AWS ECR and run as tasks on AWS ECS. The code can also be modified to handle batch predicts with some modifications.
AWS Lambda functions turned out to be not suitable for this due to size limitaions.
## CI/CD
To achieve CI/CD, use GitHub Actions. Configure the CI/CD pipeline to trigger any updates whenever changes are pushed to the main branch.  <br>
- Create a file 'ci.yml' in directory 
```.github/worflows```<br>
- In your repository, under ```settings -> secrtes and variable```, sadd AWS access and secret keys<br>
- Set the key names as env variables in ci.yml along with AWS region<br>
- define you CI/CD workflow such as printing the branch name on push<br>
- Updaating zip file of AWS lambda function whenever there is push (code update for lambda) (included only for demo)

#### Future: 
- The pipeline can be set to trigger retraining<br>
- Rebuild docker images and push to AWS ECR  







