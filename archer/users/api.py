# -*- test-case-name: archer.users.tests.test_api -*-

import json

from twisted.internet.defer import inlineCallbacks, returnValue

from treq import post, content

from aludel.service import service, handler, get_json_params

NEO4J_URL = 'http://localhost:7474'


@inlineCallbacks
def cypher_query(query, params=None):
    params = params or {}
    resp = yield post(NEO4J_URL + '/db/data/cypher', json.dumps({
        "query": query,
        "params": params,
    }), headers={
        'Accept': ['application/json; charset=UTF-8'],
        'Content-Type': ['application/json'],
    })
    body = yield content(resp)
    returnValue(body)


@service
class UserServiceApp(object):

    def __init__(self, conn_str, reactor):
        pass

    @handler('/', methods=['PUT'])
    @inlineCallbacks
    def create_user(self, request):
        props = get_json_params(
            request, ["username", "password", "email", "msisdn"])
        response = yield cypher_query(
            "CREATE (user:User { props }) RETURN user", {
                "props": props
            })
        returnValue(json.loads(response))
