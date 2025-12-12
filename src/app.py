from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/greet')
def greet():
    return jsonify({'message': 'Hello from the backend!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
