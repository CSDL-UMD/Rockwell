import psycopg2
import json
import os

DB_URL = os.getenv("DATABASE_URL")

APP_HOME = os.path.dirname(__file__) + "/../../"

def run_schema_sql(conn):
    with conn.cursor() as cur:
        with open(APP_HOME + "schema.sql", "r") as f:
            cur.execute(f.read())
        conn.commit()

def insert_sample_tweets(conn):
    with open(APP_HOME + "sample_posts.json", "r") as f:
        tweets = json.load(f)["data"]
    
    with conn.cursor() as cur:
        for tweet in tweets:
            cur.execute("""
                INSERT INTO tweets (id, data)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (int(tweet["id"]), json.dumps(tweet)))
        conn.commit()

def get_tweets(conn, number):
    cur = conn.cursor()
    
    cur.execute(f"SELECT data FROM tweets ORDER BY id DESC LIMIT {number};")
    rows = cur.fetchall()

    cur.close()

    # Each row is a tuple like: (data,)
    return [row[0] for row in rows]
