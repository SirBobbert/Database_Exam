import os
import pyodbc
from dotenv import load_dotenv
from flask import Flask, request, jsonify

import endpoints

app = Flask(__name__)

load_dotenv()
db_pw = os.getenv("MSSQL_PW")

# Endpoint for executing the stored procedure
@app.route('/api/executeStoredProc/<userID>', methods=['POST'])
def execute_stored_procedure(userID):
    # Parse the request data
    order_lines = endpoints.get_all_cart_products(userID)

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
