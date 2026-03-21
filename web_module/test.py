import json
import string
import mysql.connector
from pathlib import Path
config_path = Path(__file__).resolve().parent.parent / "naq" / "config.json"

# Load config
with open(config_path, "r") as f:
    config = json.load(f)


# Connect to MySQL
conn = mysql.connector.connect(
    host=config["host"],
    port=config["port"],
    user=config["user"],
    password=config["password"],
    database=config["name"]
)

'''print("Connected!")

cursor = conn.cursor()
cursor.execute("SELECT DATABASE();")

for row in cursor:
    print("Current DB:", row)

cursor.close()
conn.close()'''

from naq import schema_loader


print(schema_loader._fetch_schema_mysql(conn,config["name"]))