import socket
from time import sleep
import logging as log
import threading
from http.server import HTTPServer
from flask import Flask, render_template, Response, request
from prometheus_client import start_http_server, Summary, MetricsHandler, Counter, generate_latest

app = Flask(__name__)
PROMETHEUS_PORT = 9000
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'DESC: Time spent processing request')
INDEX_TIME = Summary('index_request_processing_seconds', 'DESC: INDEX time spent processing request')

# Create a metric to cound the number of runs on process_request()
c = Counter('requests_for_host', 'Number of runs of the process_request method', ['method', 'endpoint'])

@app.route('/')
@INDEX_TIME.time()
def hello_world():
    path = str(request.path)
    verb = request.method
    label_dict = {"method": verb,
                 "endpoint": path}
    c.labels(**label_dict).inc()

    return 'Flask Dockerized'

# Decorate function with metric.
def process_request():
    """A dummy function that takes some time."""
    sleep(2)

    fqdn = socket.getfqdn()
    return fqdn

@app.route('/host')
def host():
    path = str(request.path)
    verb = request.method
    label_dict = {"method": verb,
                  "endpoint": path}
    c.labels(**label_dict).inc()

    ret = str(process_request())
    return "The name of this host is: {}".format(ret)

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# Seperate web server for prometheus scraping
class PrometheusEndpointServer(threading.Thread):
    """A thread class that holds an http and makes it serve_forever()."""
    def __init__(self, httpd, *args, **kwargs):
        self.httpd = httpd
        super(PrometheusEndpointServer, self).__init__(*args, **kwargs)

    def run(self):
        self.httpd.serve_forever()

# keep the server running
def start_prometheus_server():
    try:
        httpd = HTTPServer(("0.0.0.0", PROMETHEUS_PORT), MetricsHandler)
    except (OSError, socket.error):
        return

    thread = PrometheusEndpointServer(httpd)
    thread.daemon = True
    thread.start()
    log.info("Exporting Prometheus /metrics/ on port %s", PROMETHEUS_PORT)

start_prometheus_server()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
