from flask import Flask
app = Flask(__name__)
app.debug = True
app.config['WTF_CSRF_ENABLED'] = True
app.secret_key = 's3cr3t'

# Create a metric to track time spent and requests made.
INDEX_TIME = Summary('index_request_processing_seconds', 'DESC: INDEX time spent processing request')

# Create a metric to count the number of runs on process_request()
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

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
