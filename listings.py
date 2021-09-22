from flask import Flask, render_template, jsonify
from flask_restful import Resource, Api, reqparse
from datetime import datetime, timedelta
import mysql.connector
from flask import Flask, request
import json
import api

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

class Listings(Resource):
    def get(self):
        cursor = db.cursor(buffered=True)
        inventory_list = []
        check = ("SELECT id_Storage, item_name, expiry_date, quantity FROM Storage ORDER BY expiry_date")
        cursor.execute(check)
        for (id_Storage, item_name, expiry_date, quantity) in cursor:
            # print("{} of {} expiring by {:%d %b %Y}".format(item_name, quantity, expiry_date))
            # inventory_list.append(Listing(item_name=item_name, expiry_date=expiry_date, quantity=quantity))
            item = {'id':id_Storage,'item_name':item_name, "expiry_date":str(expiry_date), "quantity":quantity}
            inventory_list.append(item)
        db.close()
        return json.dumps(inventory_list)

    def post(self):
        data = json.loads(request.data.decode('utf-8'))
        # print(type(data))
        # print(data)
        # print('LOL')
        item = data['item_name']
        date = data['expiry_date']
        amount = data['amount']
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

    def delete(self):
        res = {}
        reslst = []
        data = json.loads(request.data.decode('utf-8'))
        item = data['item']
        amount = data['amount']
        db = mysql.connector.connect(**config)
        cursor = db.cursor(buffered=True)
        amount_wanted = amount
        res['amount'] = amount_wanted
        res['item'] = item
        # check if the item exists or not.
        check = ("SELECT item_name FROM Storage WHERE item_name = %s")
        cursor.execute(check, (item,))
        data = cursor.fetchall()
        if not data:
            # print("No such item in inventory.")
            db.close()
            return "No such item in inventory.", 401
        else:
            query = ("SELECT quantity FROM Storage WHERE item_name = %s")
            cursor.execute(query, (item,))
            total_amount_in_fridge = 0
            amount_of_one_listing = 0
            deleted_amount = 0
            expiry_date_list = []
            for (quantity_total,) in cursor:
                total_amount_in_fridge += quantity_total
            if amount > total_amount_in_fridge:
                # print("Not enough items in inventory.")
                db.close()
                return "Not enough items in inventory.", 401
            else:
                # print("Enough items: {} wanted, {} in storage.".format(amount_wanted, total_amount_in_fridge))
                query = ("SELECT expiry_date FROM Storage WHERE item_name = %s ORDER BY expiry_date ASC")
                cursor.execute(query, (item,))
                for (expiry_date,) in cursor:
                    expiry_date_list.append(expiry_date)
                for listing_expiry_date in expiry_date_list:
                    if amount > 0:
                        amount_of_one_listing = 0
                        query = ("SELECT id_Storage, quantity FROM Storage WHERE item_name = %s AND expiry_date = %s")
                        cursor.execute(query, (item, listing_expiry_date))
                        row = cursor.fetchone()
                        amount_of_one_listing += row[0]
                        # for (quantity,) in cursor:
                        #     amount_of_one_listing += quantity
                        if amount >= amount_of_one_listing:
                            query = ("DELETE FROM Storage WHERE item_name = %s AND expiry_date = %s")
                            cursor.execute(query, (item, listing_expiry_date,))
                            db.commit()
                            deleted_amount += amount_of_one_listing                        
                            amount -= amount_of_one_listing
                        else:
                            query = ("UPDATE Storage SET quantity = quantity - %s WHERE item_name = %s AND expiry_date = %s")
                            cursor.execute(query, (amount, item, listing_expiry_date,))
                            db.commit()
                            deleted_amount += amount
                            amount = 0
                # print("Delete {} of {} successfully!".format(item, amount_wanted))
                db.close()
                return 'Success'


api.add_resource(Listings, '/listings')  # add endpoints

if __name__ == '__main__':
    api.run()  # run our Flask app