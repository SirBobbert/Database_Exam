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
















def find_category_by_product_id(product_id):
    # Define the Cypher query to retrieve the category based on the product ID
    query = f"""
    MATCH (product:Product {{id: '{product_id}'}})
    MATCH (product)-[:CATEGORIZED_AS]->(category:Category)
    RETURN category.name AS Category
    """

    # Execute the query and retrieve the category
    with driver.session() as session:
        result = session.run(query)
        category = result.single()["Category"]

    # Close the Neo4j driver
    driver.close()

    return category


@app.route('/category/<product_id>', methods=['GET'])
def category_endpoint(product_id):
    category = find_category_by_product_id(product_id)
    return jsonify({"Category": category})










if __name__ == '__main__':
    app.run()
