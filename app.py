from os import name
from flask.wrappers import Response
import mysql.connector
from flask import Flask, request
import json
from datetime import datetime, timedelta
import requests
from mysql.connector import cursor
from werkzeug.wrappers import response
from flask_cors import CORS

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

def inDate(stringdate):
    datedate = datetime.strptime(stringdate, "%Y-%m-%d %H:%M:%S").replace(minute=0, hour=0, second=0)
    return datedate


app = Flask(__name__)
CORS(app)

@app.route('/listings', methods=['GET']) # Get the list of items in the fridge. done
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

@app.route('/listings', methods=['POST']) # Check in an item into the fridge. done
def addItem():
    data = json.loads(request.data.decode('utf-8'))
    item = data['item']
    date = inDate(data['expiry_date'])
    amount = data['amount']
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    # check if the item existed already or not.
    check = ("SELECT item_name FROM Storage WHERE item_name = %s AND expiry_date = %s")
    cursor.execute(check, (item, date,))
    have = cursor.fetchall()
    if have:
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

@app.route('/listings', methods=['DELETE']) # Check out an item from the fridge. done
def takeItem():
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
    have = cursor.fetchall()
    if not have:
        # print("No such item in inventory.")
        db.close()
        return json.dumps(["No such item in inventory."])
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
                        reslst.append({'id': id_Storage, 'item': item, 'amount': 0, 'expiry_date':str(listing_expiry_date)})
                        deleted_amount += amount_of_one_listing                        
                        amount -= amount_of_one_listing
                    else:
                        query = ("UPDATE Storage SET quantity = quantity - %s WHERE item_name = %s AND expiry_date = %s")
                        cursor.execute(query, (amount, item, listing_expiry_date,))
                        db.commit()
                        reslst.append({'id': id_Storage, 'item': item, 'amount': amount_of_one_listing-amount, 'expiry_date':str(listing_expiry_date)})
                        deleted_amount += amount
                        amount = 0
            # print("Delete {} of {} successfully!".format(item, amount_wanted))
            res['lst'] = reslst
            db.close()
            return json.dumps(res)

@app.route('/listingdetails', methods=['DELETE'])
def deleteItem():
    data = json.loads(request.data.decode('utf-8'))
    itemId = data['id']
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    check = ("SELECT item_name FROM Storage WHERE id_Storage = %s")
    cursor.execute(check, (itemId,))
    have = cursor.fetchall()
    if not have:
        # print("No such item in inventory.")
        db.close()
        return json.dumps(["No such item in inventory."])
    else:
        query = ("DELETE FROM Storage WHERE id_Storage = %s")
        cursor.execute(query, (itemId,))
        db.commit()
        db.close()
        return json.dumps(data)

@app.route('/listings', methods=['PUT']) # Change the information of a listing. done
def updateItem():
    data = json.loads(request.data.decode('utf-8'))
    id_Storage = data['id']
    item = data['item']
    amount = data['amount']
    date = inDate(data['expiry_date'])
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    query = ("UPDATE Storage SET item_name = %s, quantity = %s, expiry_date = %s WHERE id_Storage = %s")
    cursor.execute(query, (item, amount, date, id_Storage))
    db.commit()
    db.close()
    print("Updated an existing item: {} of {} expiring by {:%d %b %Y}.".format(item, amount, date))
    return data

@app.route('/recipes', methods=['GET']) # Get the list of recipes in the database. done
def checkRecipe():
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    recipe_list = []
    check = ("SELECT id_Recipe, recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4 FROM Recipe ORDER BY id_Recipe")
    cursor.execute(check)
    for (id_Recipe, recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4) in cursor:
        if ingredient_1 == None:
            ingredient_1 = 'Null'
        if ingredient_2 == None:
            ingredient_2 = 'Null'
        if ingredient_3 == None:
            ingredient_3 = 'Null'
        if ingredient_4 == None:
            ingredient_4 = 'Null'
        a_recipe = {'id':id_Recipe, 'name':recipe_name, 'ingredient_1':ingredient_1, 'ingredient_2':ingredient_2, 'ingredient_3':ingredient_3, 'ingredient_4':ingredient_4}
        recipe_list.append(a_recipe)
    db.commit()
    db.close()
    return json.dumps(recipe_list)

@app.route('/recipes', methods=['POST']) # Add another recipe into the database. done
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
    cursor.execute(check, (name,))
    have = cursor.fetchall()
    if have:
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

@app.route('/recipes', methods=['DELETE']) # Delete an existing recipe from the database. done
def deleteRecipe():
    data = json.loads(request.data.decode('utf-8'))
    id_Recipe = data['id']
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    check = ("SELECT recipe_name FROM Recipe WHERE id_Recipe = %s")
    cursor.execute(check, (id_Recipe,))
    ok = cursor.fetchall()
    if ok:
        query = ("DELETE FROM Recipe WHERE id_Recipe = %s")
        cursor.execute(query, (id_Recipe,))
        db.commit()
        db.close()
        return json.dumps(data)
    else:
        print("No such recipe.")
        return json.dumps(["No such recipe."])

@app.route('/recipes', methods=['PUT']) # Change an existing recipe's information. done
def updateRecipe():
    data = json.loads(request.data.decode('utf-8'))
    id_Recipe = data['id']
    name = data['name']
    ingredient_1 = data['ingredient_1']
    ingredient_2 = data['ingredient_2']
    ingredient_3 = data['ingredient_3']
    ingredient_4 = data['ingredient_4']
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    # check if the recipe exists or not
    check = ("SELECT recipe_name FROM Recipe WHERE id_Recipe = %s")
    cursor.execute(check, (id_Recipe,))
    have = cursor.fetchall()
    if have:
        query = ("UPDATE Recipe SET recipe_name = %s, ingredient_1 = %s, ingredient_2 = %s, ingredient_3 = %s, ingredient_4 = %s WHERE id_Recipe = %s")
        cursor.execute(query, (name, ingredient_1, ingredient_2, ingredient_3, ingredient_4, id_Recipe))
        db.commit()
        print("Changed an existing recipe: {} needs {}, {}, {}, {}.".format(name, ingredient_1, ingredient_2, ingredient_3, ingredient_4))
        db.close()
        return json.dumps(data)
    else:
        print("No such recipe.")
        db.close()
        return json.dumps(["No such recipe."])

@app.route('/recom', methods=['GET']) # Get recommended list of recipes depending on the expiring foods. done
def recomRecipe():
    recom_recipe_list = []
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    expiring_lst = []
    check = ("SELECT item_name FROM Storage WHERE expiry_date = %s ORDER BY expiry_date")
    cursor.execute(check, (tomorrow,))
    for (item_name,) in cursor:
        expiring_lst.append(item_name)
    print('Expiring_lst:', expiring_lst)
    inventory_lst = []
    check = ("SELECT item_name FROM Storage ORDER BY expiry_date")
    cursor.execute(check)
    for (item_name,) in cursor:
        item = item_name
        inventory_lst.append(item)
    print("Inventory_lst:", inventory_lst)
    recipe_lst = []
    check = ("SELECT id_Recipe, recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4 FROM Recipe ORDER BY id_Recipe")
    cursor.execute(check)
    for (id_Recipe, recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4) in cursor:
        if ingredient_1 == None:
            ingredient_1 = 'Null'
        if ingredient_2 == None:
            ingredient_2 = 'Null'
        if ingredient_3 == None:
            ingredient_3 = 'Null'
        if ingredient_4 == None:
            ingredient_4 = 'Null'
        a_recipe = {'id':id_Recipe, 'name':recipe_name, 'ingredient':[ingredient_1, ingredient_2, ingredient_3, ingredient_4]}
        recipe_lst.append(a_recipe)
    print('Recipe_lst:', recipe_lst)
    for recipe in recipe_lst:
        for item in expiring_lst:
            if item in recipe['ingredient']:
                if all(foo in inventory_lst for foo in [x for x in recipe['ingredient'] if x != "Null"]):
                    print(recipe)
                    if recipe not in recom_recipe_list:
                        recom_recipe_list.append(recipe) 
    return json.dumps(recom_recipe_list)

@app.route('/recom', methods=['POST'])
def getspecificRecipe():
    data = json.loads(request.data.decode('utf-8'))
    SPingredient = data['item']
    recom_recipe_list = []
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    expiring_lst = []
    check = ("SELECT item_name FROM Storage WHERE expiry_date = %s ORDER BY expiry_date")
    cursor.execute(check, (tomorrow,))
    for (item_name,) in cursor:
        expiring_lst.append(item_name)
    print('Expiring_lst:', expiring_lst)
    inventory_lst = []
    check = ("SELECT item_name FROM Storage ORDER BY expiry_date")
    cursor.execute(check)
    for (item_name,) in cursor:
        item = item_name
        inventory_lst.append(item)
    print("Inventory_lst:", inventory_lst)
    recipe_lst = []
    check = ("SELECT id_Recipe, recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4 FROM Recipe ORDER BY id_Recipe")
    cursor.execute(check)
    for (id_Recipe, recipe_name, ingredient_1, ingredient_2, ingredient_3, ingredient_4) in cursor:
        if ingredient_1 == None:
            ingredient_1 = 'Null'
        if ingredient_2 == None:
            ingredient_2 = 'Null'
        if ingredient_3 == None:
            ingredient_3 = 'Null'
        if ingredient_4 == None:
            ingredient_4 = 'Null'
        a_recipe = {'id':id_Recipe, 'name':recipe_name, 'ingredient':[ingredient_1, ingredient_2, ingredient_3, ingredient_4]}
        recipe_lst.append(a_recipe)
    print('Recipe_lst:', recipe_lst)
    for recipe in recipe_lst:
        for item in expiring_lst:
            if item in recipe['ingredient']:
                if all(SPingredient in recipe['ingredient'] and foo in inventory_lst for foo in [x for x in recipe['ingredient'] if x != "Null"]):
                    print(recipe)
                    if recipe not in recom_recipe_list:
                        recom_recipe_list.append(recipe) 
    return json.dumps(recom_recipe_list)

@app.route('/listingdetails', methods=['GET']) 
def getExpiry():
    db = mysql.connector.connect(**config)
    cursor = db.cursor(buffered=True)
    expiring_list = []
    check = ("SELECT id_Storage, item_name, expiry_date, quantity FROM Storage WHERE expiry_date < %s ORDER BY expiry_date")
    print(threedays)
    cursor.execute(check, (threedays,))
    for (id_Storage, item_name, expiry_date, quantity) in cursor:
        item = {'id':id_Storage,'item':item_name, "expiry_date":str(expiry_date), "amount":quantity}
        expiring_list.append(item) 
    db.close()
    return expiring_list


if __name__ == "__main__":
    app.run(host='0.0.0.0')