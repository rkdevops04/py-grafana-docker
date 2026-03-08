from flask import Flask
from prometheus_client import start_http_server, Summary
import time

app = Flask(__name__)
metrics = Summary('request_duration_seconds', 'Duration of requests in seconds')

@app.route('/')
@metrics.timeit
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    start_http_server(8000)
    app.run(host='0.0.0.0')
