from flask import Flask,request,g,jsonify
app = Flask(__name__)
import datetime
import time
import random
timestamps = []
@app.before_request
def start_time():
    now = time.time()
    dt = datetime.datetime.fromtimestamp(now)
    timestamp = dt
    g.start = timestamp
    timestamps.append(g.start)

# @app.after_request
# def print_request():
#     print(str(g.start))

@app.route('/process/',methods = ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def entrypoint():
    response = {}
    time1 = random.randint(15,30)
    time.sleep(time1)
    response["Time"] = g.start
    response["Method"] = request.method
    # response_string = str(request.method)+" Request Recieved at "+str(g.start)+" Responded at "+str(datetime.datetime.fromtimestamp(time.time()))
    # print("Response String ",response_string)
    response["Header"] = dict(request.headers)
    response["Query"]= request.args
    # print("Request Header",request.headers)
    # print("Request Query",request.args)
    response["Body"]= request.json
    # print("Request Data",request.json)
    response["duration"]= time1
    return jsonify(response)

if __name__=='__main__':
    app.run(debug = False,port=5000)
