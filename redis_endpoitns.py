from flask import Flask, request, jsonify
import redis

app = Flask(__name__)

r = redis.Redis(
    host='redis-16589.c250.eu-central-1-1.ec2.cloud.redislabs.com',
    port=16589,
    password='3HPSWVLu0KdknewcZ3WCn3ndZydtZioH')

def get_key_from_redis(key):
    data = r.get(key)
    return data

def get_hashtable_from_redis(key):
    data = r.hgetall(key)
    data = {k.decode(): v.decode() for k, v in data.items()}
    return data




# Endpoint for retrieving keys from Redis
@app.route('/api/getKey/<key>', methods=['GET'])
def get_key(key):
    data = get_key_from_redis(key)
    if data is None:
        return jsonify({"message": "Key not found"})
    else:
        return jsonify({"value": data.decode()})
    

    
    
# Endpoint for retrieving hashtables from Redis
@app.route('/api/getHash/<key>', methods=['GET'])
def get_hash(key):
    data = get_hashtable_from_redis(key)
    if data is None:
        return jsonify({"message": "Key not found"})
    else:
        return jsonify({"value": data})
    




if __name__ == '__main__':
    app.run()
