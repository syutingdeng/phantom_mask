from flask import Flask, request, jsonify
import sqlite3
import re


app = Flask(__name__)

def query_db(query, args=(), one=False):
    #計算相關性分數
    conn = sqlite3.connect('mask.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, args)
    rv = [dict(row) for row in cursor.fetchall()]   
    conn.close()
    return rv if rv else None

@app.route('/', methods=['GET'])
def index():
   return "Hello World"

@app.route('/pharmacies/open', methods=['GET'])
def list_open_pharmacies():
    try:
        day = request.args.get('day')
        time = request.args.get('time')
        #檢查是否符合時間格式:
        if re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$",time):
            hh = int(time.split(":")[0])
            mm = int(time.split(":")[1])
            mm = hh * 60 + mm
            query = '''
            SELECT name, openingHours FROM pharmacies
            Join opening op on pharmacies.id = op.pharmacy_id
            WHERE op.openingDay LIKE ? and
            op.openingTime <= ? and
            op.closedTime >= ?
            '''
            args = (f"%{day}%",mm,mm)
            print(args)
            pharmacies = query_db(query, args)
            print(pharmacies)
            return jsonify(pharmacies)
        else:
            return jsonify({"error": "Incorrect data formate"}),400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route('/masks/by_pharmacy', methods=['GET'])
def list_masks_by_pharmacy():
    pharmacy_name = request.args.get('pharmacyName')
    sort_by = request.args.get('sortBy') # 'name' or 'price'
    print(sort_by)
    query = '''
    SELECT masks.name, masks.price FROM masks
    JOIN pharmacies ON masks.pharmacy_id = pharmacies.id
    WHERE pharmacies.name = ?
    ORDER BY masks.{}
    '''.format(sort_by)
    
    args = (pharmacy_name,)
    masks = query_db(query, args)
    return jsonify(masks)

@app.route('/pharmacies/with_masks', methods=['GET'])
def list_pharmacies_with_mask_count():
    mask_count = request.args.get('maskCount', type=int)
    more_or_less = request.args.get('moreOrLess')
    price_min = request.args.get('priceMin', type=float)
    price_max = request.args.get('priceMax', type=float)
    print(more_or_less,mask_count,price_min,price_max)
    
    #
    query = '''
    SELECT pharmacies.name, COUNT(masks.id) as X FROM pharmacies
    JOIN masks ON pharmacies.id = masks.pharmacy_id
    Where masks.price BETWEEN ? AND ?
    GROUP BY pharmacies.id
    HAVING COUNT(masks.id) {operator} ? 
    '''.format(operator='>' if more_or_less=="more" else '<')
    args = (price_min, price_max,mask_count)
    pharmacies = query_db(query, args)
    return jsonify(pharmacies)

@app.route('/top_users', methods=['GET'])
def top_users():
    top_x = request.args.get('topX', type=int)
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    print(start_date,end_date)
    query = '''
    SELECT customers.name, SUM(transaction_amount) AS total_amount
    FROM purchase_histories
    JOIN customers on customers.id = purchase_histories.customer_id
    WHERE transaction_date BETWEEN ? AND ?
    GROUP BY purchase_histories.customer_id
    ORDER BY total_amount DESC
    LIMIT ?
    '''
    
    args = (f"{start_date}", f"{end_date}", top_x)
    users = query_db(query, args)
    return jsonify(users)

@app.route('/total_mask', methods=['GET'])
def total_mas():
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    query = '''
    SELECT COUNT(*) AS total_masks, SUM(transaction_amount) AS total_amount
    FROM purchase_histories
    WHERE transaction_date BETWEEN ? AND ?
    '''
    
    args = (start_date, end_date)
    totals = query_db(query, args, one=True)
    return jsonify(totals)

@app.route('/search', methods=['GET'])
def search():
    term = request.args.get('term')
    query = '''
    SELECT *, bm25(name_fts) AS relevance
    FROM name_fts
    WHERE name_fts MATCH ?
    ORDER BY relevance DESC;
    '''
    args = (term,)
    results = query_db(query, args)
    return jsonify(results)

@app.route('/purchase', methods=['POST'])
def purchase():
    data = request.json
    conn = sqlite3.connect('mask.db')
    cursor = conn.cursor()
    
    try:
        #先檢查是該店家是否有指定產品
        cursor.execute('SELECT id FROM masks WHERE name = ? and pharmacy_id = ?', (data['mask_name'], data['pharmacy_id']))
        print(cursor.fetchone)
        if not cursor.fetchone():
            return jsonify({"NoProduct": "店家沒有指定商品"}), 400
        
        # Start transaction
        conn.execute('BEGIN TRANSACTION')
        
        # 加入消費紀錄
        cursor.execute('''
        INSERT INTO purchase_histories (customer_id, pharmacy_id, mask_name, transaction_amount, transaction_date)
        VALUES (?, ?, ?, ?, ?)
        ''', (data['customer_id'], data['pharmacy_id'], data['mask_name'], data['transaction_amount'], data['transaction_date']))
        
        # 更新藥局餘額
        cursor.execute('''
        UPDATE pharmacies
        SET cashBalance = cashBalance + ?
        WHERE id = ?
        ''', (data['transaction_amount'], data['pharmacy_id']))
        
        # Commit transaction
        conn.commit()
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)