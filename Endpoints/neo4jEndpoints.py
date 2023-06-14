import redis
from flask import jsonify
from neo4j import GraphDatabase

# Redis config
r = redis.Redis(
    host='redis-16589.c250.eu-central-1-1.ec2.cloud.redislabs.com',
    port=16589,
    password='3HPSWVLu0KdknewcZ3WCn3ndZydtZioH')

# Neo4j config
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "changeme"))

#----------------------------------------------------------------------------------------------------------------------------------------

# Helper function
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

#----------------------------------------------------------------------------------------------------------------------------------------

# Returns 50 products based on category
def view_all_products(category):
    category = category.capitalize()
    query = """
    MATCH (category:Category {name:'""" + category + """'})
    MATCH (product:Product)-[:CATEGORIZED_AS]->(category)
    RETURN product LIMIT 50
    """
    products = execute_query_and_process_result(query)
    return jsonify(products)

#----------------------------------------------------------------------------------------------

# Finds top 15 best rated products in the same category as the productID's category
def matching_products(productID):
    category = find_top_products(productID)
    return jsonify({"Category": category})

def find_top_products(productID):
    category_query = f"""
    MATCH (product:Product {{id: '{productID}'}})
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

#----------------------------------------------------------------------------------------------

# Shows top 10 most popular categories using the degree centrality algorithm
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

#----------------------------------------------------------------------------------------------------------------------------------------