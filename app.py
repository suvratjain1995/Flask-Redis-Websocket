from flask import Flask,request,g,jsonify
from multiprocessing import Queue
app = Flask(__name__)
import datetime
import time
import random
import redis
from rq import Queue
from rq.job import Job
from worker import conn
import json
import pickle
# q = Queue(connection=conn)
class Records:
    records = []
    def __init__(self):
        pass

redisClient = redis.StrictRedis(host='localhost',port=6379,db=0)
redisClient.set('post',0)
redisClient.set('get',0)
redisClient.set('put',0)
redisClient.set('delete',0)
r = Records()
@app.before_request
def start_time():
    now = time.time()
    dt = datetime.datetime.fromtimestamp(now)   
    timestamp = dt
    g.start = timestamp
    if request.method == "POST":
        redisClient.incr('post')
    if request.method == "GET":
        redisClient.incr('get')
    if request.method == "PUT":
        redisClient.incr('put')
    if request.method == "DELETE":
        redisClient.incr('delete')

def set_request_value(request):
    if request.method == "POST":
        redisClient.decr('post')
    if request.method == "GET":
        redisClient.decr('get')
    if request.method == "PUT":
        redisClient.decr('put')
    if request.method == "DELETE":
        redisClient.decr('delete')

def average_request(reponse_list,method_name):
    average_request_result = 0
    for responses in reponse_list:
        if responses["Method"] == method_name:
            average_request_result+=responses["duration"]
    if len(reponse_list)>0:
        return average_request_result/len(reponse_list)
    else:
        return 0;

def number_of_method_request(response_list,method_name):
    number_of_request = 0;
    for responses in response_list:
        if responses["Method"] == method_name:
            number_of_request+=1
    return number_of_request;

def save_incoming_request(response):
    Records.records.append(response)
    redisClient.rpush("records",pickle.dumps(response))

def get_active_request():
    response = {}
    response["POST"] = int(redisClient.get('post'))
    response["PUT"] = int(redisClient.get('put'))
    response["GET"] = int(redisClient.get('get'))
    response["DELETE"] = int(redisClient.get('delete'))
    return response

def minute_stat(method_list):
    valid_responses = []
    current_time = g.start
    records = []
    for i in range(0,redisClient.llen('records')):
        records.append(pickle.loads(redisClient.lindex('records',i)))
    for responses in records:
        temp_recieve_time = responses["Time"]
        if temp_recieve_time.day == current_time.day and \
            temp_recieve_time.hour == current_time.hour and \
            temp_recieve_time.year == current_time.year and \
            temp_recieve_time.minute == current_time.minute:
            valid_responses.append(responses)
    
    minute_stat_dict = {}
    for methods in method_list:
        method_avg = methods+"_minute_avg"
        method_count = methods+"_minute_count"
        minute_stat_dict[method_avg] = average_request(valid_responses,methods)
        minute_stat_dict[method_count] = number_of_method_request(valid_responses,methods)
    return minute_stat_dict


def hour_stat(method_list):
    valid_responses = []
    current_time = g.start
    records = []
    for i in range(0,redisClient.llen('records')):
        records.append(pickle.loads(redisClient.lindex('records',i)))
    for responses in records:
        temp_recieve_time = responses["Time"]
        if temp_recieve_time.day == current_time.day and \
            temp_recieve_time.hour == current_time.hour and \
            temp_recieve_time.year == current_time.year:
            valid_responses.append(responses)
    
    hour_stat_dict = {}
    for methods in method_list:
        method_avg = methods+"_hour_avg"
        method_count = methods+"_hour_count"
        hour_stat_dict[method_avg] = average_request(valid_responses,methods)
        hour_stat_dict[method_count] = number_of_method_request(valid_responses,methods)
    return hour_stat_dict


def general_stat(method_list):
    general_stat_dict = {}
    for methods in method_list:
        method_avg = methods+"_hour_avg"
        method_count = methods+"_hour_count"
        general_stat_dict[method_avg] = average_request(Records.records,methods)
        general_stat_dict[method_count] = number_of_method_request(Records.records,methods)
    return general_stat_dict

@app.route('/stats',methods = ['GET', 'POST', 'PUT', 'DELETE'])
def get_stat():
    response = {}
    set_request_value(request)
    response["minute_stat"] = minute_stat(['GET', 'POST', 'PUT', 'DELETE'])
    response["hour_stat"] = hour_stat(['GET', 'POST', 'PUT', 'DELETE'])
    response["general_stat"] = general_stat(['GET', 'POST', 'PUT', 'DELETE'])
    response["active_request"] = get_active_request();
    
    return jsonify(response)




@app.route('/process/',methods = ['GET', 'POST', 'PUT', 'DELETE'])
def entrypoint():
    response = {}
    time1 = random.randint(15,30)
    time.sleep(time1)
    response["Time"] = g.start
    response["Method"] = request.method
    response["Header"] = dict(request.headers)
    response["Query"]= request.args
    response["Body"]= request.json
    response["duration"]= time1
    save_incoming_request(response)
    set_request_value(request)
    return jsonify(response)
    


if __name__=='__main__':
    app.run(debug = True,port=5000)
