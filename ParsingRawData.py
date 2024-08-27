import sqlite3
import json
from datetime import datetime
import re
import os

def insert_data_to_sqlite():
    
    #讀取資料，連接DB
    with open("users.json","r") as file:
        data1 = json.load(file)
        
    with open("pharmacies.json","r") as file:
        data2 = json.load(file)

    
    if os.path.exists("mask.db"):
        print("初始化DB")
        os.remove("mask.db")
    
    
    conn = sqlite3.connect('mask.db')
    cursor = conn.cursor()
    
    #建Table 購買紀錄
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cash_balance REAL NOT NULL
        )
    ''')
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_histories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            pharmacy_name TEXT NOT NULL,
            mask_name TEXT NOT NULL,
            transaction_amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    #建table 使用者
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pharmacies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cashBalance REAL,
            openingHours TEXT
        )
    ''')
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opening (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            openingTime TEXT,
            closedTime Text,
            openingDay Text,
            pharmacy_id INTEGER,
            FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(id)
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS masks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL,
            pharmacy_id INTEGER,
            FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(id)
        )
    ''')
    
    
    #建立sqlite fts相關性tabel
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS name_fts USING fts5(
        name,
    )
    ''')
    
    #insert fts
    name_fts_insert ='''
    INSERT OR IGNORE INTO name_fts (name)
    VALUES (?)
    '''
    
    
    
    # insert sql 
    customer_insert = '''
    INSERT INTO customers (name, cash_balance)
    VALUES (?, ?)
    '''
   
    purchase_history_insert = '''
        INSERT INTO purchase_histories (customer_id, pharmacy_name, mask_name, transaction_amount, transaction_date)
        VALUES (?, ?, ?, ?, ?)
    '''

    
    pharmacy_insert = '''
            INSERT INTO pharmacies (name, cashBalance, openingHours)
            VALUES (?, ?, ?)
        '''
    
   
    opening_insert = '''
        INSERT INTO opening (openingTime, closedTime, openingDay, pharmacy_id)
        VALUES (?, ?, ?, ?)
        '''
    
    mask_insert = '''
        INSERT INTO masks (name, price, pharmacy_id)
                VALUES (?, ?, ?)
        '''
    
    for customer in data1:
        
        cursor.execute(customer_insert, (customer["name"], customer["cashBalance"]))
        customer_id = cursor.lastrowid

     
        purchase_histories = []
        for record in customer['purchaseHistories']:
            purchase_histories.append((
                customer_id,
                record['pharmacyName'],
                record['maskName'],
                record['transactionAmount'],
                record['transactionDate']
            ))
            
            
 
        cursor.executemany(purchase_history_insert, purchase_histories)
        
    

    for pharmacy in data2:
        
        cursor.execute(pharmacy_insert, (pharmacy["name"], pharmacy["cashBalance"], pharmacy["openingHours"]))
        pharmacy_id = cursor.lastrowid
        
        cursor.execute(name_fts_insert,(pharmacy["name"],))
        
        for mask in pharmacy["masks"]:
            cursor.execute(name_fts_insert,(mask["name"],))

        openings = []
        for time in pharmacy["openingHours"].split("/"):
            weekday = ",".join(re.findall(r"(Mon|Tue|Wed|Thur|Fri|Sat|Sun)",time))
            weektimeOpen = re.findall(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})',time)[0][0]
            weektimeclosed = re.findall(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})',time)[0][1]
            openings.append((
                int(weektimeOpen.split(":")[0])*60+int(weektimeOpen.split(":")[1]),
                int(weektimeclosed.split(":")[0])*60+int(weektimeclosed.split(":")[1]),
                weekday,
                pharmacy_id
            ))
        cursor.executemany(opening_insert,openings)
        masks = [(mask["name"], mask["price"], pharmacy_id) for mask in pharmacy["masks"]]
        cursor.executemany(mask_insert, masks)
   
        #重新對應pharmacy_Name & pharmacy_id
    cursor.execute("ALTER TABLE purchase_histories ADD COLUMN pharmacy_id INTEGER;")
    cursor.execute('''
                UPDATE purchase_histories
                SET pharmacy_id = (
                    SELECT id
                    FROM pharmacies
                    WHERE pharmacies.name = purchase_histories.pharmacy_name
                );
                ''')
    cursor.execute("ALTER TABLE purchase_histories DROP COLUMN pharmacy_Name;")
   
    conn.commit()
    conn.close()
    

  

if __name__ == '__main__':
    insert_data_to_sqlite()