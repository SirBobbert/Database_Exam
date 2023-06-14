from Endpoints.redisEndpoints import update_popular_products_in_redis, get_products_from_redis, add_cart_product, remove_cart_product, get_all_cart_products
from Endpoints.neo4jEndpoints import view_all_products, matching_products, popular_categories
from Endpoints.sqlEndpoints import  insert_products
# Setup your routing framework or call the endpoints directly as needed

# Example using Flask
from flask import Flask

app = Flask(__name__)

# Redis endpoints
app.route('/redis/updateRedis', methods=['GET'])(update_popular_products_in_redis)
app.route('/redis/products', methods=['GET'])(get_products_from_redis)
app.route('/redis/addCartProduct', methods=['POST'])(add_cart_product)
app.route('/redis/removeCartProduct', methods=['POST'])(remove_cart_product)
app.route('/redis/getCart/<userID>', methods=['GET'])(get_all_cart_products)

# Neo4j endpoints
app.route('/neo4j/productsFromCategory/<category>', methods=['GET'])(view_all_products)
app.route('/neo4j/matchingProducts/<productID>', methods=['GET'])(matching_products)
app.route('/neo4j/popularCategories/', methods=['GET'])(popular_categories)

# SQL endpoints
app.route('/sql/insertProducts/<userID>', methods=['POST'])(insert_products)

if __name__ == '__main__':
    app.run()
