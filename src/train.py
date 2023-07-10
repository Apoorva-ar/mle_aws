import os
import zipfile
import boto3
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import joblib
from dotenv import load_dotenv
load_dotenv()
import json
from datetime import date

def zip_files(files, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                zipf.write(file)


def get_dataset() -> pd.DataFrame:
    s3_bucket = os.getenv('DATA_STORE')

    s3_client = boto3.client("s3")
    response = s3_client.list_objects_v2(Bucket=s3_bucket)

    if 'Contents' in response:
        latest_file = max(response['Contents'], key=lambda obj: obj['LastModified'])
        latest_file_key = latest_file['Key']

        s3_client.download_file(s3_bucket, latest_file_key, "data.csv")

        df = pd.read_csv("data.csv", index_col=0)
        return df
    raise ValueError("No file found in the S3 bucket.")
    

def preprocess_dataset(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = LabelEncoder().fit_transform(df[column])
    return df

def scale_dataset(df: pd.DataFrame) -> tuple[np.array, np.array, object]:
    X = np.array(df.drop(["churn"], axis=1))
    y = np.array(df["churn"])
    scaler = MinMaxScaler()
    scaler.fit(X)
    X = scaler.transform(X)
    return X, y, scaler

def split_dataset(X: np.array, y: np.array) -> tuple[np.array, 
                                                     np.array,np.array, np.array]:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1)
    return X_train, X_test, y_train, y_test

def train_model(X_train: np.array, X_test: np.array, 
                y_train: np.array, y_test: np.array) -> tuple[float, object]:
    clf = xgb.XGBClassifier(
        n_estimators=1000,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.2,
    )
    clf.fit(X_train, y_train)
    accuracy = clf.score(X_test, y_test)
    return accuracy, clf

def save_model(clf: object, scaler: object, accuracy: float) -> None:
    s3_bucket = os.getenv('MODEL_ARTIFACTS_STORE')
    s3_resource = boto3.resource("s3")
    s3_bucket_obj = s3_resource.Bucket(s3_bucket)
    model_dir = 'models'

    response = s3_bucket_obj.meta.client.list_objects_v2(Bucket=s3_bucket)
    if 'Contents' in response:
        objects = response['Contents']
        # Extract the versions from the file names
        versions = [obj['Key'].split('_')[1].split('.')[0] for obj in objects if 'model_' in obj['Key']]
    # Calculate the latest version
    else:
        versions = [0]
    latest_version = max(versions, default='0')
    new_version = str(int(latest_version) + 1)

    model_path = os.path.join(model_dir, f'model_{new_version}.xgb')
    scaler_path = os.path.join(model_dir,  f'scaler_{new_version}.pkl')

    clf.save_model(model_path)
    joblib.dump(scaler, scaler_path)

    s3_bucket_obj.upload_file(model_path, model_path)
    s3_bucket_obj.upload_file(scaler_path, scaler_path)

    # Store model metadata
    metadata = {
        'version': new_version,
        'scaler': scaler_path,
        'accuracy': accuracy,
        'training_date': date.today().strftime('%Y-%m-%d')
    }

    metadata_json = json.dumps(metadata)
    s3_bucket_obj.put_object(
        Key=os.path.join(model_dir, f'metadata_{new_version}.json'),
        Body=metadata_json
    )
    # zip artifacts
    output_zip = os.path.join(model_dir, f'model_af_{new_version}.zip')
    zip_files([model_path,scaler_path], output_zip)


def run_training() -> None:
    df = get_dataset()
    df = preprocess_dataset(df)
    X, y, scaler = scale_dataset(df)
    X_train, X_test, y_train, y_test = split_dataset(X, y)
    accuracy, clf = train_model(X_train, X_test, y_train, y_test)
    save_model(clf, scaler, accuracy)
    print("Model training completed.")

def lambda_handler():
    run_training()


if __name__ == "__main__":
   run_training()