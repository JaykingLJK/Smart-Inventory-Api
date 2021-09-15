from flask.wrappers import Response
import mysql.connector
from flask import Flask, request
import json
from datetime import datetime, timedelta
import requests
from mysql.connector import cursor

config = {
  'user': 'admin',
  'password': 'fuckJayking!',
  'host': 'ee3080e012.cywdkmac2vws.ap-southeast-1.rds.amazonaws.com',
  'database': 'ee3080',
  'raise_on_warnings': True
}
db = mysql.connector.connect(**config)
today = datetime.now().replace(minute=0, hour=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
today = datetime.strptime(today, '%Y-%m-%d %H:%M:%S')
tomorrow = today + timedelta(days=1)
threedays = today + timedelta(days=3)

app = Flask(__name__)

@app.route('/listings', methods=['GET'])
def checkInventory():
    cursor = db.cursor(buffered=True)
    inventory_list = []
    check = ("SELECT item_name, expiry_date, quantity FROM Storage ORDER BY expiry_date")
    cursor.execute(check)
    for (item_name, expiry_date, quantity) in cursor:
        # print("{} of {} expiring by {:%d %b %Y}".format(item_name, quantity, expiry_date))
        # inventory_list.append(Listing(item_name=item_name, expiry_date=expiry_date, quantity=quantity))
        item = {'item_name':item_name, "expiry_date":str(expiry_date), "quantity":quantity}
        inventory_list.append(item)
    db.close()
    return json.dumps(inventory_list)

@app.route('/listings', methods=['POST'])
def addItem():
    if request.is_json:
        item = request.form['item_name']
        date = request.form['expiry_date']
        amount = request.form['amount']
        db = mysql.connector.connect(**config)
        cursor = db.cursor(buffered=True)
        # check if the item existed already or not.
        check = ("SELECT item_name FROM Storage WHERE item_name = %s AND expiry_date = %s")
        date = today + timedelta(days=date)
        cursor.execute(check, (item, date,))
        data = cursor.fetchall()
        if data:
            query = ("UPDATE Storage SET quantity = quantity + %s WHERE item_name = %s AND expiry_date = %s")
            cursor.execute(query, (amount, item, date,))
            db.commit()
            print("Added an existing item: {} of {} expiring by {:%d %b %Y}.".format(item, amount, date))
        else:
            query = ("INSERT INTO Storage (item_name, expiry_date, quantity) VALUES (%s, %s, %s);")
            cursor.execute(query, (item, date, amount))
            db.commit()
            print("Added a new item: {} of {} expiring by {:%d %b %Y}.".format(item, amount, date))
        db.close()
        return 'Success'
    else:
        return 'Failure'
class Listing():
    def __init__(self, item_name, expiry_date, quantity):

        self.item_name = item_name
        self.expiry_date = expiry_date
        self.quantity = quantity
 