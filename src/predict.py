import os
import boto3
import numpy as np
import pandas as pd
import xgboost as xgb
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from flask import Flask, request
import joblib
from dotenv import load_dotenv
load_dotenv()

def preprocess_dataset(df):
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = LabelEncoder().fit_transform(df[column])
    return df

def predict_classes(X, clf):
    return clf.predict_proba(X, iteration_range=(0, 10))

def save_results(data: np.array, results: np.array, version: str) -> None:
    s3_bucket = os.getenv("RESULTS_STORE")
    # s3 = boto3.client("s3")
    access_key = os.getenv("AWS_ACCESS_KEY")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    s3 = boto3.client("s3", aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    df = pd.DataFrame(np.concatenate((data, results.reshape(1, -1)), axis=1))
    df["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    results_file_path = f"results_{version}.csv"
    s3_key = f"{results_file_path}"

    existing_file = s3.list_objects(Bucket=s3_bucket, Prefix='results')
    if 'Contents' in existing_file:
        response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        existing_data = response['Body'].read().decode('utf-8')
        csv_data = df.to_csv(index=False, header=False)
        updated_data = existing_data + csv_data
    else:
        csv_data = df.to_csv(index=False)
        updated_data = csv_data

    s3.put_object(Body=updated_data, Bucket=s3_bucket, Key=s3_key)

@app.route('/inference', methods=['POST'])
def run_inference():
    data = request.json['data']
    model_version = request.json['model_version'] 

    s3_bucket = os.getenv('MODEL_ARTIFACTS_STORE')

    model_dir = 'models'
    model_file_path = f"{model_dir}/model_{model_version}.xgb"
    scaler_file_path = f"{model_dir}/scaler_{model_version}.pkl"

    # s3 = boto3.client("s3")
    access_key = os.getenv("AWS_ACCESS_KEY")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    s3 = boto3.client("s3", aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    s3.download_file(s3_bucket, model_file_path, model_file_path)
    s3.download_file(s3_bucket, scaler_file_path, scaler_file_path)

    # Load model
    clf = xgb.XGBClassifier()
    clf.load_model(model_file_path)

    # Load scaler
    scaler = joblib.load(scaler_file_path)
    
    # Preprocess data
    df = pd.DataFrame(data, columns=["Country", "Count", "id",])
    df = preprocess_dataset(df)
    X = np.array(df)
    X = scaler.transform(X)

    # Perform inference
    results = predict_classes(X, clf)

    # Save results
    save_results(df,results, model_version)
    return ("Inference completed.")

# def lambda_handler(event, context):
#     try:
#         data = event['data']
#         model_version = event['model_version']
#         run_inference(data, model_version)
#         return {
#             'statusCode': 200,
#             'body': 'Inference completed successfully.'
#         }
#     except Exception as e:
#         return {
#             'statusCode': 500,
#             'body': str(e)
#         }
if __name__ == '__main__':
    app = Flask(__name__)
    app.run(host='0.0.0.0', port=8000)
    print("Flask application started")

    
