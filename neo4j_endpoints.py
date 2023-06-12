from flask import Flask, jsonify, request
from neo4j import GraphDatabase

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

def convert_node_to_dict(node):
    return dict(node)


def execute_query_and_process_result(query):
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))
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





if __name__ == '__main__':
    app.run()
