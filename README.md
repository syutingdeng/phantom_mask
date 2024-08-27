# phantom_mask_api

安裝說明:  
Python 版本: 3.11.3  
安裝套件 pip install -r requirements.txt

檔案說明:  
ParsingRawData.py: 處理資料並加入 mask.db  
mask.db: sqlite DB File  
app.py:主程式

執行方式:  
第一次使用或需要重新進行資料轉換至 DB 時執行 ParsingRawData.py  
接著執行 app.py 啟動服務

1.List all pharmacies open at a specific time and on a day of the week if requested.  
Path: /pharmacies/open  
HTTP Method: GET  
Params:
|Key|Value|  
|----|----|  
|day|Mon,Tue,Wed,Thur,Fri,Sat,Sun|  
|time|00:00~23:59|

Response:
|Key|Value|  
|----|----|  
|name|藥局名稱|
|openingHours|開門時間|

2.List all masks sold by a given pharmacy, sorted by mask name or price.
Path: /masks/by_pharmacy
HTTP Method: GET  
Params:
|Key|Value|  
|----|----|  
|pharmacyName|藥局名稱(Text)|  
|sortBy|price,name|

Response:
|Key|Value|  
|----|----|  
|name|商品名稱|
|price|價格|

3.List all pharmacies with more or less than x mask products within a price range.  
Path:/pharmacies/with_masks  
HTTP Method: GET  
Params:
|Key|Value|  
|----|----|  
|maskCount|數量(int)|  
|moreOrLess|more,less|
|priceMin|價格下限|  
|priceMax|價格上限|

Rsponse:
|Key|Value|  
|----|----|  
|X|產品數量|
|name|藥局名稱|

4.The top x users by total transaction amount of masks within a date range.
Path:/top_users
HTTP Method: GET  
Params:
|Key|Value|  
|----|----|  
|topX|上限數量(int)|  
|startDate|開始時間(YYYY-MM-DD HH:MM:SS)|
|endDate|結束時間(YYYY-MM-DD HH:MM:SS)|

Rsponse:
|Key|Value|  
|----|----|  
|name|消費者|
|total_amount|消費金額|

5.The total amount of masks and dollar value of transactions within a date range.

Path: /total_mask
HTTP Method: GET  
Params:
|Key|Value|  
|----|----|  
|startDate|開始時間(YYYY-MM-DD HH:MM:SS)|
|endDate|結束時間(YYYY-MM-DD HH:MM:SS)|

Rsponse:
|Key|Value|  
|----|----|  
|total_amount|時間內總金額|
|total_masks|時間內範圍產品數|

6.Search for pharmacies or masks by name, ranked by relevance to the search term.
Path: /search
HTTP Method: GET  
Params:
|Key|Value|  
|----|----|  
|term|要搜尋的文字|

Rsponse:
|Key|Value|  
|----|----|  
|name|搜尋結果(pharmacies or masks name)|

##補充說明: 這裡計算相關度的方式使用 sqlite fts-5 & BM25 來計算相關性

7.Process a user purchases a mask from a pharmacy, and handle all relevant data changes in an atomic transaction.

Path: /purchase
HTTP Method: Post

Request Body:

| Key                | Value           |
| ------------------ | --------------- |
| customer_id        | 消費者的唯一 id |
| pharmacy_id        | 藥局唯一 id     |
| mask_name          | 商品名稱        |
| transaction_amount | 交易金額        |
| transaction_date   | 交易日期        |

Respons:
200 Success:順利更新
400:
|類型|說明|
| -|-|
|NoProduct|店家沒有指定商品|
|error|Exception and Roll back TRANSACTION|

#補充說明:
實作增加購買紀錄以及更新藥局餘額兩項功能
更新前會檢查商家是否有指定商品
