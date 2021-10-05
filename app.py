from os import name
from flask.wrappers import Response
import mysql.connector
from flask import Flask, request
import json
from datetime import datetime, timedelta
import requests
from mysql.connector import cursor
from werkzeug.wrappers import response

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
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    inventory_list = []
    check = ("SELECT id_Storage, item_name, expiry_date, quantity FROM Storage ORDER BY expiry_date")
    cursor.execute(check)
    for (id_Storage, item_name, expiry_date, quantity) in cursor:
        # print("{} of {} expiring by {:%d %b %Y}".format(item_name, quantity, expiry_date))
        # inventory_list.append(Listing(item_name=item_name, expiry_date=expiry_date, quantity=quantity))
        item = {'id':id_Storage,'item':item_name, "expiry_date":str(expiry_date), "amount":quantity}
        inventory_list.append(item)
    db.close()
    return json.dumps(inventory_list)

@app.route('/listings', methods=['POST'])
def addItem():
    data = json.loads(request.data.decode('utf-8'))
    # print(type(data))
    # print(data)
    # print('LOL')
    item = data['item']
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
    return json.dumps(data)

@app.route('/listings', methods=['DELETE'])
def deleteItem():
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
            return json.dumps(["not enough in inventory"])
        else:
            # print("Enough items: {} wanted, {} in storage.".format(amount_wanted, total_amount_in_fridge))
            query = ("SELECT expiry_date FROM Storage WHERE item_name = %s ORDER BY expiry_date ASC")
            cursor.execute(query, (item,))
            for (expiry_date,) in cursor:
                expiry_date_list.append(expiry_date)
            for listing_expiry_date in expiry_date_list:
                if amount > 0:
                    amount_of_one_listing = 0
                    query = ("SELECT quantity, id_Storage FROM Storage WHERE item_name = %s AND expiry_date = %s")
                    cursor.execute(query, (item, listing_expiry_date))
                    row = cursor.fetchone()
                    amount_of_one_listing += row[0]
                    id_Storage = row[1]
                    # for (quantity,) in cursor:
                    #     amount_of_one_listing += quantity
                    if amount >= amount_of_one_listing:
                        query = ("DELETE FROM Storage WHERE item_name = %s AND expiry_date = %s")
                        cursor.execute(query, (item, listing_expiry_date,))
                        db.commit()
                        reslst.append({'id': id_Storage, 'item': item, 'amount': 0, 'expiry_date':listing_expiry_date})
                        deleted_amount += amount_of_one_listing                        
                        amount -= amount_of_one_listing
                    else:
                        query = ("UPDATE Storage SET quantity = quantity - %s WHERE item_name = %s AND expiry_date = %s")
                        cursor.execute(query, (amount, item, listing_expiry_date,))
                        db.commit()
                        reslst.append({'id': id_Storage, 'item': item, 'amount': amount_of_one_listing-amount, 'expiry_date':listing_expiry_date})
                        deleted_amount += amount
                        amount = 0
            # print("Delete {} of {} successfully!".format(item, amount_wanted))
            res['lst'] = reslst
            db.close()
            return json.dumps(res)

@app.route('/listings', methods=['PUT'])
def updateItem():
    data = json.loads(request.data.decode('utf-8'))
    id = data['id']
    item = data['item']
    amount = data['amount']
    date = data['expiry_date']
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    query = ("UPDATE Storage SET item_name = %s, quantity = %s, expiry_date = %s WHERE id_Storage = %s")
    cursor.execute(query, (item, amount, date, id))
    db.commit()
    db.close()
    print("Updated an existing item: {} of {} expiring by {:%d %b %Y}.".format(item, amount, date))
    return data

@app.route('/recipes', method=['GET'])
def checkRecipe():
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    recipe_list = []
    check = ("SELECT id_Recipe, recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4 FROM Recipe ORDER BY id_Recipe")
    cursor.execute(check)
    for (id_Recipe, recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4) in cursor:
        a_recipe = {'id':id_Recipe, 'name':recipe_name, 'ingredient_1':ingredient_1, 'ingredient_2':ingredient_2, 'ingredient_3':ingredient_3, 'ingredient_4':ingredient_4}
        recipe_list.append(a_recipe)
    db.commit()
    db.close()
    return json.dump(recipe_list)

@app.route('/recipes', method=['POST'])
def addRecipe():
    data = json.loads(request.data.decode('utf-8'))
    name = data['name']
    ingredient_1 = data['ingredient_1']
    ingredient_2 = data['ingredient_2']
    ingredient_3 = data['ingredient_3']
    ingredient_4 = data['ingredient_4']
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    # check if the recipe exists or not
    check = ("SELECT recipe_name FROM Recipe WHERE recipe_name = %s")
    cursor.execute(check, (name))
    data = cursor.fetchall()
    if data:
        query = ("UPDATE Recipe SET ingredient_1 = %s, ingredient_2 = %s, ingredient_3 = %s, ingredient_4 = %s WHERE recipe_name = %s")
        cursor.execute(query, (ingredient_1, ingredient_2, ingredient_3, ingredient_4, name))
        db.commit()
        print("Changed an existing recipe: {} needs {}, {}, {}, {}.".format(name, ingredient_1, ingredient_2, ingredient_3, ingredient_4))
    else:
        query = ("INSERT INTO Recipe (recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4) VALUES (%s, %s, %s, %s, %s);")
        cursor.execute(query, (name, ingredient_1, ingredient_2, ingredient_3, ingredient_4))
        db.commit()
        print("Added a new recipe: {} needs {}, {}, {}, {}.".format(name, ingredient_1, ingredient_2, ingredient_3, ingredient_4))
    db.close()
    return json.dumps(data)



if __name__ == "__main__":
    app.run(host='0.0.0.0')