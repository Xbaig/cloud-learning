import os
import time
import json
import boto3
import psycopg2
from dotenv import load_dotenv

load_dotenv()

sqs = boto3.client("sqs", region_name="us-east-1")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def process_message(body):
    data = json.loads(body)
    conn = get_connection()
    cur = conn.cursor()
    message_text = f"{data['company_name']} moved from {data['old_status']} to {data['new_status']}"
    cur.execute(
        "INSERT INTO notifications (application_id, event_type, message) VALUES (%s, %s, %s)",
        (data["application_id"], data["event_type"], message_text)
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Processed: {message_text}")

while True:
    response = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=10)
    messages = response.get("Messages", [])
    for msg in messages:
        process_message(msg["Body"])
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])