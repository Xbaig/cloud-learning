import os
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import boto3
import json
from datetime import datetime, timezone

sqs = boto3.client("sqs", region_name="us-east-1")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")

load_dotenv()

app = FastAPI()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

class Application(BaseModel):
    company_name: str
    role_title: str
    status: str = "applied"
    date_applied: str
    follow_up_date: str | None = None
    notes: str | None = None

@app.post("/applications")
def create_application(app_data: Application):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO applications (company_name, role_title, status, date_applied, follow_up_date, notes) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (app_data.company_name, app_data.role_title, app_data.status, app_data.date_applied, app_data.follow_up_date, app_data.notes)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "status": "created"}

@app.get("/applications")
def list_applications():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, company_name, role_title, status, date_applied, follow_up_date, notes FROM applications ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    columns = ["id", "company_name", "role_title", "status", "date_applied", "follow_up_date", "notes"]
    return [dict(zip(columns, row)) for row in rows]




class StatusUpdate(BaseModel):
    new_status: str

@app.patch("/applications/{app_id}/status")
def update_status(app_id: int, update: StatusUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT company_name, status FROM applications WHERE id = %s", (app_id,))
    row = cur.fetchone()
    if row is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Application not found")

    company_name, old_status = row
    cur.execute(
        "UPDATE applications SET status = %s, updated_at = NOW() WHERE id = %s",
        (update.new_status, app_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    message = {
        "event_type": "status_changed",
        "application_id": app_id,
        "company_name": company_name,
        "old_status": old_status,
        "new_status": update.new_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))

    return {"id": app_id, "status": update.new_status}