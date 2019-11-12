# /usr/bin/env python3

import os

import ipaddress
import json
import requests
import yaml

import hashlib
import hmac

from flask import Flask, request, abort, Response

import redis
import rq
from gwmh.job import mkdocs_job

HTTP_STATUS_OK = 200
HTTP_STATUS_ACCEPTED = 202
HTTP_STATUS_NO_CONTENT = 204
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_FORBIDDEN = 403


def parse_config(path):
    with open(path) as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    if not 'webhook_path' in config.keys():
        config['webhook_path'] = '/'

    if not 'secret_token' in config.keys():
        config['secret_token'] = None

    if not 'verify_github_ip' in config.keys():
        config['verify_github_ip'] = False

    return config


config = parse_config('config.yaml')
app = Flask(__name__)

redis_conn = redis.Redis(unix_socket_path='/var/run/redis/redis-server.sock')
rq_queue = rq.Queue(connection=redis_conn)


@app.route(config['webhook_path'], methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return 'Successfully reached webhook server with GET request.'.encode('utf-8'), HTTP_STATUS_OK
    elif request.method == 'POST':

        if config['verify_github_ip']:
            if not verify_github_remote_addr():
                abort(Response("Request originated from invalid IP address".encode('utf-8'),
                               status=HTTP_STATUS_FORBIDDEN, content_type="text/plain"))

        if not config['secret_token'] is None:
            if not verify_github_secret_token():
                abort(Response("Invalid secret token".encode('utf-8'),
                               status=HTTP_STATUS_FORBIDDEN, content_type="text/plain"))

        if not request.is_json:
            abort(Response("Content-Type must be application/json".encode('utf-8'),
                           status=HTTP_STATUS_BAD_REQUEST, content_type="text/plain"))

        if not is_push_event():
            abort(Response("Payload was not a push event. Aborting.".encode('utf-8'),
                           status=HTTP_STATUS_ACCEPTED, content_type="text/plain"))

        if not is_target_repo():
            abort(Response("Payload was not for the target repository. Aborting.".encode('utf-8'),
                           status=HTTP_STATUS_ACCEPTED, content_type="text/plain"))

        if not is_target_branch():
            abort(Response("Payload was not for a target branch. Aborting.".encode('utf-8'),
                           status=HTTP_STATUS_ACCEPTED, content_type="text/plain"))

        queue_mkdocs_job()
        return Response('Successfully queued mkdocs build job for {}, {} branch. Exiting.'.format(get_repository(), get_branch()).encode('utf-8'),
                        status=HTTP_STATUS_OK, content_type="text/plain")


def get_repository():
    return request.json['repository']['full_name']


def get_branch():
    return request.json['ref'].split('/')[-1]


def get_output_path():
    return config['repositories'][get_repository()][get_branch()]


def verify_github_remote_addr():
    github_ips = requests.get('https://api.github.com/meta').json()['hooks']
    for ip in github_ips:
        if ipaddress.ip_address(request.remote_addr.encode('utf-8')) in ipaddress.ip_network(ip.encode('utf-8')):
            return True
    return False


def verify_github_secret_token():

    if not config['secret_token'] is None:
        token = config['secret_token']
    else:
        return False

    if not request.headers.has_key('X-Hub-Signature'):
        return False
    received = request.headers['X-Hub-Signature']

    h = hashlib.new('sha1')
    h.update(token)
    h.update(request.data)
    expected = 'sha1=' + h.hexdigest()

    return hmac.compare_digest(received.encode('utf-8'), expected)


def is_push_event():
    if request.headers.has_key('X-GitHub-Event'):
        return request.headers['X-GitHub-Event'] == 'push'
    else:
        return False


def is_target_repo():
    return get_repository() in config['repositories'].keys()


def is_target_branch():
    return request.json['ref'] in ['refs/heads/{}'.format(b)
                                   for b in config['repositories'][get_repository()]]


def queue_mkdocs_job():
    rq_queue.enqueue(mkdocs_job,
                     get_repository(), get_branch(), get_output_path())
