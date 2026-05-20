import csv
import os
from datetime import datetime

import mysql.connector

from dotenv import load_dotenv

# --------------------------------
# LOAD ENV VARIABLES
# --------------------------------

load_dotenv()

# --------------------------------
# CONNECT TO RAILWAY MYSQL
# --------------------------------

db = mysql.connector.connect(

    host=os.getenv("MYSQLHOST"),

    user=os.getenv("MYSQLUSER"),

    password=os.getenv("MYSQLPASSWORD"),

    database=os.getenv("MYSQLDATABASE"),

    port=int(os.getenv("MYSQLPORT"))

)

cursor = db.cursor()

print("Connected to Railway MySQL!")

# --------------------------------
# OPEN CSV FILE
# --------------------------------

with open(

    'catalog.csv',

    newline='',

    encoding='utf-8'

) as file:

    reader = csv.DictReader(file)

    for row in reader:

        try:

            # ------------------------
            # HANDLE PRICES
            # ------------------------

            base_price = (

                float(row['base_price'])

                if row['base_price']

                else 0

            )

            offer_price = (

                float(row['offer_price'])

                if row['offer_price']

                else base_price

            )

            # ------------------------
            # HANDLE DATES
            # ------------------------

            listed_date = None

            if row['listed_date']:

                listed_date = datetime.strptime(

                    row['listed_date'],

                    "%d-%m-%Y"

                ).strftime("%Y-%m-%d")

            stock_last_updated = None

            if row['stock_last_updated']:

                stock_last_updated = datetime.strptime(

                    row['stock_last_updated'],

                    "%d-%m-%Y"

                ).strftime("%Y-%m-%d")

            # ------------------------
            # INSERT INTO DATABASE
            # ------------------------

            cursor.execute("""

                INSERT INTO Catalog (

                    product_id,
                    product_name,
                    category,
                    brand,
                    model,
                    base_price,
                    offer_price,
                    product_status,
                    listed_date,
                    stock_last_updated,
                    gst_percent

                )

                VALUES (

                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s

                )

            """, (

                row['product_id'],

                row['product_name'],

                row['category'],

                row['brand'],

                row['model'],

                base_price,

                offer_price,

                row['product_status'],

                listed_date,

                stock_last_updated,

                18

            ))

        except Exception as e:

            print(

                "Error importing row:",

                row,

                "\n",

                e

            )

# --------------------------------
# SAVE CHANGES
# --------------------------------

db.commit()

print("Import Complete!")

cursor.close()

db.close()