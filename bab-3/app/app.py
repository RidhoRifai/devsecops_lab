import os
from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

@app.route("/")
def health():
    try:
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
        )
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return jsonify({"status": "ok", "database": db_status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
