from flask import Flask, Response
import mysql.connector
import os

app = Flask(__name__)

# Environment variables for MySQL connection
DB_HOST = os.getenv("DB_HOST", "#####")
DB_PORT = os.getenv("DB_PORT", "#####")
DB_USER = os.getenv("DB_USER", "#####")  # Optional, default user
DB_PASSWORD = os.getenv("DB_PASSWORD", "#####")  # Optional, default password
DB_NAME = os.getenv("DB_NAME", "#####")  # Optional, default database


@app.route("/is-db-alive", methods=["GET"])
def is_db_alive():
    try:
        # Attempt to connect to the database
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        connection.close()
        return Response("DB is alive", status=200)
    except mysql.connector.Error as err:
        return Response(f"DB connection failed: {err}", status=500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
