


query = ("SELECT id_Storage, quantity FROM Storage WHERE item_name = %s AND expiry_date = %s")
cursor.execute(query, (item, listing_expiry_date))
row = cursor.fetchone()