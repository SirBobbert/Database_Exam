from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from flask import Flask, request, jsonify
import networkx as nx

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

def convert_node_to_dict(node):
    return dict(node)

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))

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






# Takes a category as parameter, then returns 50 products
@app.route('/products/<category>', methods=['GET'])
def get_products(category):
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

    # Close the Neo4j driver
    driver.close()

    return top_products

@app.route('/findMatchingProducts/<product_id>', methods=['GET'])
def category_endpoint(product_id):
    category = find_top_products(product_id)
    return jsonify({"Category": category})



# Shows top 10 categories based on the degree centrality algorithm
@app.route('/topCategories', methods=['GET'])
def top_categories_endpoint():
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



# Finds top 10 items with the highest average rating
@app.route('/topItems', methods=['GET'])
def top_items_endpoint():
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

    return jsonify({"items": items})



if __name__ == '__main__':
    app.run()
