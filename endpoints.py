import networkx as nx
import redis
import json
import os
import pyodbc

from flask import Flask, app, jsonify, request
from dotenv import load_dotenv
from neo4j import GraphDatabase

app = Flask(__name__)

# Load ENV variables
load_dotenv()

# Redis config
r = redis.Redis(
    host='redis-16589.c250.eu-central-1-1.ec2.cloud.redislabs.com',
    port=16589,
    password='3HPSWVLu0KdknewcZ3WCn3ndZydtZioH')

# Neo4j config
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))

# SQL server config



# Helper functions for Redis
def get_hashtable_from_redis(key):
    data = r.hgetall(key)
    data = {k.decode(): v.decode() for k, v in data.items()}
    return data

# Helper functions for Neo4j
def convert_node_to_dict(node):
    return dict(node)

def execute_query_and_process_result(query):
    with driver.session() as session:
        result = session.run(query)
        records = []
        for record in result:
            node = record["product"]
            node_dict = convert_node_to_dict(node)
            records.append(node_dict)

    session.close()
    driver.close()
    return records

# Endpoints

# Returns 50 products based on category
@app.route('/products/<category>', methods=['GET'])
def view_all_products(category):
    category = category.capitalize()
    query = """
    MATCH (category:Category {name:'""" + category + """'})
    MATCH (product:Product)-[:CATEGORIZED_AS]->(category)
    RETURN product LIMIT 50
    """
    products = execute_query_and_process_result(query)
    return jsonify(products)

# Takes productID as parameter
# Finds top 15 products based on average rating
# Based on ProductID
@app.route('/findMatchingProducts/<product_id>', methods=['GET'])
def matching_products(product_id):
    category = find_top_products(product_id)
    return jsonify({"Category": category})

def find_top_products(product_id):
    category_query = f"""
    MATCH (product:Product {{id: '{product_id}'}})
    MATCH (product)-[:CATEGORIZED_AS]->(category:Category)
    RETURN category.name AS Category
    """
    with driver.session() as session:
        category_result = session.run(category_query)
        category = category_result.single()["Category"]

    top_products_query = f"""
    MATCH (product:Product)-[:CATEGORIZED_AS]->(:Category {{name: '{category}'}})
    RETURN product
    ORDER BY product.`Average Rating` DESC
    LIMIT 15
    """

    with driver.session() as session:
        result = session.run(top_products_query)
        top_products = [dict(record["product"]) for record in result]

    driver.close()

    return top_products

# Shows top 10 most popular categories
# based on the degree centrality algorithm
@app.route('/popularCategories', methods=['GET'])
def popular_categories():
    query = """
    MATCH (c:Category)
    OPTIONAL MATCH (p:Product)-[:CATEGORIZED_AS]->(c)
    WITH c, count(p) AS degreeCentrality
    ORDER BY degreeCentrality DESC
    RETURN c.name AS name, degreeCentrality
    LIMIT 10
    """

    with driver.session() as session:
        result = session.run(query)
        categories = [{"name": record["name"], "degreeCentrality": record["degreeCentrality"]} for record in result]

    return jsonify({"categories": categories})

# Takes the top 50 most popular products based on average rating
# And writes it to Redis
@app.route('/updateRedis', methods=['GET'])
def update_popular_products_in_redis():
    query = """
    MATCH (p:Product)
    WITH p, p.`Average Rating` AS averageRating
    ORDER BY averageRating DESC
    RETURN p
    LIMIT 50
    """

    with driver.session() as session:
        result = session.run(query)
        items = [dict(record["p"]) for record in result]

    # Store items in Redis as a hashset
    redis_key = "popular_products"
    
    # Delete the existing hashtable
    r.delete(redis_key)

    # Update Redis with the new data
    redis_data = {str(i): json.dumps(items[i]) for i in range(len(items))}
    r.hmset(redis_key, redis_data)

    return jsonify({"Products": items})

# Returns the top 50 popular products data written to Redis
@app.route('/popularProducts', methods=['GET'])
def get_products_from_redis():
    redis_key = "popuar_products"
    data = get_hashtable_from_redis(redis_key)
    return jsonify(data)


def get_hashtable_from_redis(key):
    data = r.hgetall(key)
    parsed_data = {}
    for k, v in data.items():
        key_str = k.decode()
        value_json = v.decode()
        parsed_data[key_str] = json.loads(value_json)
    return parsed_data




# Add product in redis
@app.route('/addCartProduct/', methods=['POST'])
def add_cart_product():
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    product_data = request.json['product_data']

    # Convert product_data dictionary to JSON string
    product_data_json = json.dumps(product_data)

    # Set the Hash Set in Redis
    r.hset('Cart:' + user_id, product_id, product_data_json)

    return 'Hash Set created successfully'


# Remove product in redis
@app.route('/removeCartProduct/', methods=['POST'])
def remove_cart_product():
    user_id = request.json['user_id']
    product_id = request.json['product_id']

    # Set the Hash Set in Redis
    r.hdel('Cart:' + user_id, product_id)

    return 'Product removed successfully'



# Show all products in redis
@app.route('/getAllCartProducts/<userID>', methods=['GET'])
def get_all_cart_products(userID):
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

    response_data = order_lines

    return jsonify(response_data)


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

load_dotenv()
db_pw = os.getenv("MSSQL_PW")

# Endpoint for executing the stored procedure
@app.route('/api/executeStoredProc/<userID>', methods=['POST'])
def execute_stored_procedure(userID):
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

if __name__ == '__main__':
    app.run()