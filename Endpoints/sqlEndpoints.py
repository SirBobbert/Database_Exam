import redis, json, os, pyodbc
from flask import jsonify
from dotenv import load_dotenv

# Redis config
r = redis.Redis(
    host='redis-16589.c250.eu-central-1-1.ec2.cloud.redislabs.com',
    port=16589,
    password='3HPSWVLu0KdknewcZ3WCn3ndZydtZioH')

# Load ENV
load_dotenv()
db_pw = os.getenv("MSSQL_PW")

#----------------------------------------------------------------------------------------------------------------------------------------

# Helper function
def get_all_cart_products_for_sql(userID):
    cart_data = r.hgetall('Cart:' + str(userID))

    order_lines = []
    for key, value in cart_data.items():
        product_id = int(key.decode())
        product_data = json.loads(value.decode())
        order_lines.append({
            "product_id": product_id,
            "product_name": product_data["name"],
            "quantity": product_data["quantity"],
            "price": product_data["price"]
        })

    return order_lines

#----------------------------------------------------------------------------------------------------------------------------------------

# Endpoint for executing the stored procedure
def insert_products(userID):
    # Parse the request data
    order_lines = get_all_cart_products_for_sql(userID)

    # Establish a connection to the SQL Server database
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost;'
        'PORT=1433;'
        'DATABASE=DBExam;'
        'UID=sa;'
        'PWD=' + db_pw + ';'
    )

    # Create a cursor object to execute SQL statements
    cursor = conn.cursor()

    try:
        # Generate the INSERT INTO statements for each order line
        insert_statements = []
        for line in order_lines:
            product_id = line['product_id']
            product_name = line['product_name']
            quantity = line['quantity']
            price = line['price']

            insert_statement = f"INSERT INTO @typeOrderLines(productID, productName, quantity, price) VALUES ({product_id}, '{product_name}', {quantity}, {price})"
            insert_statements.append(insert_statement)

        # Combine the INSERT INTO statements into a single SQL query
        insert_query = "; ".join(insert_statements)

        # Execute the stored procedure
        cursor.execute(f"DECLARE @typeOrderLines OrderLinesType, @userID int; SET @userID = ?; {insert_query}; EXEC dbo.InsertOrderWithOrderLines @userID, @typeOrderLines", userID)

        # Commit the transaction
        conn.commit()

        # Remove the Redis hashmap
        r.delete('Cart:' + str(userID))


        # Return the response as JSON
        return jsonify({'message': 'Stored procedure executed successfully'})

    except Exception as e:
        # Rollback the transaction in case of any error
        conn.rollback()
        # Optionally, handle the exception and return an error response
        return jsonify({'error': str(e)})

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
#----------------------------------------------------------------------------------------------------------------------------------------