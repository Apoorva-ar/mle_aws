import boto3

def empty_s3_bucket(bucket_name):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    # Delete all objects within the bucket
    bucket.objects.all().delete()

    # Delete all object versions within the bucket
    bucket.object_versions.all().delete()

    print(f"The bucket {bucket_name} has been emptied.")

# Replace 'my-bucket-name' with your actual bucket name
for bucket in ['train-data-apoorva','model-artifacts-apoorva','results-bucket-apoorva']:
    empty_s3_bucket(bucket)
