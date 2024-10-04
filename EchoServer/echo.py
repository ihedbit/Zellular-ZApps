from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/echo', methods=['GET', 'POST', 'PUT', 'DELETE'])
def echo():
    # Get the method of the request
    method = request.method
    # Get the data sent in the request
    data = request.get_json() if request.is_json else request.data

    # Prepare the response
    response = {
        'method': method,
        'data': data.decode('utf-8') if isinstance(data, bytes) else data
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
