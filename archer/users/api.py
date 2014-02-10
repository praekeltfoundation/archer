# -*- test-case-name: archer.users.tests.test_api -*-

import json
from uuid import uuid4

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web import http

import treq

from aludel.service import (
    service, handler, get_json_params, APIError, get_params)

NEO4J_TIMEOUT = 10
NEO4J_URL = 'http://localhost:7474'


def cypher_query(query, params=None):
    params = params or {}
    data = json.dumps({
        "query": query,
        "params": params,
    })
    return treq.post(NEO4J_URL + '/db/data/cypher', data, headers={
        'Accept': ['application/json; charset=UTF-8'],
        'Content-Type': ['application/json'],
    }, timeout=NEO4J_TIMEOUT)


def http_ok(response):
    return http.OK <= response.code < http.MULTIPLE_CHOICE


def has_node_data(json_payload):
    return json_payload['data']


def get_neo4j_data(json_payload):
    return json_payload['data'][0][0]


def get_node_data(json_payload):
    neo4j_data = get_neo4j_data(json_payload)
    return neo4j_data['data']


class UserServiceError(APIError):
    pass


@service
class UserServiceApp(object):

    def __init__(self, conn_str, reactor):
        pass

    def make_uuid(self):
        return uuid4().hex

    @handler('/users/', methods=['POST'])
    @inlineCallbacks
    def create_user(self, request):
        props = get_json_params(
            request, ["username", "email_address", "msisdn"])
        uuid = self.make_uuid()
        props.update({
            'user_id': uuid,
        })

        response = yield cypher_query(
            "CREATE (n:User { props }) RETURN n", {
                "props": props
            })
        # TODO: Figure out why the content needs to be read.
        #       Something in treq blocks on this.
        content = yield treq.content(response)
        if not http_ok(response):
            raise UserServiceError(content)

        request.redirect('/users/%s/' % (uuid,))
        returnValue({})

    @handler('/users/', methods=['GET'])
    @inlineCallbacks
    def query_users(self, request):
        params = get_params(
            request.args, [], ["username", "email_address", "msisdn"])
        if not params:
            raise UserServiceError(
                'Must provide at least of username, email_address or msisdn.',
                code=http.BAD_REQUEST)

        props = dict([(key, values[0]) for key, values in params.items()])
        search_query = " AND ".join(["n.%s = { %s }" % (key, key)
                                     for key in props])
        response = yield cypher_query(
            """
            MATCH (n:User)
            WHERE %s
            RETURN n
            """ % (search_query,), props)
        content = json.loads((yield treq.content(response)))
        returnValue({"matches": [d[0]["data"] for d in content['data']]})

    @handler('/users/<string:user_id>/relationship/')
    @inlineCallbacks
    def create_relationship(self, request, user_id):
        props = get_json_params(request, "user_id")
        response = yield cypher_query(
            """
            MATCH (this:User),(other:User)
            WHERE this.user_id = {this_user_id}
                AND other.user_id = {other_user_id}
            CREATE (this)-[r:{rel_type}]->(other)
            RETURN r
            """, {
            "this_user_id": user_id,
            "other_user_id": props["user_id"],
            "rel_type": "like",
        })
        content = yield treq.content(response)
        if not http_ok(response):
            raise UserServiceError(content)
        request.redirect('/users/%s/' % (user_id,))
        returnValue({})

    @handler('/users/<string:user_id>/', methods=['GET'])
    @inlineCallbacks
    def get_user(self, request, user_id):
        response = yield cypher_query(
            "MATCH (n:User {user_id: {user_id}}) RETURN n", {
                "user_id": user_id,
            })
        content = json.loads((yield treq.content(response)))
        if has_node_data(content):
            returnValue(get_node_data(content))

        request.setResponseCode(http.NOT_FOUND)
        returnValue({})

    @handler('/users/<string:user_id>/', methods=['PUT'])
    @inlineCallbacks
    def update_user(self, request, user_id):
        props = get_json_params(
            request, ["username", "email_address", "msisdn"])
        props.update({
            'user_id': user_id
        })

        response = yield cypher_query(
            "MATCH (n:User {user_id: {user_id}}) "
            "SET n = {props} "
            "RETURN count(n) as COUNT", {
                "user_id": user_id,
                "props": props,
            })

        content = yield treq.content(response)
        if not http_ok(response):
            raise UserServiceError(content)

        response = json.loads(content)
        count = get_neo4j_data(response)
        if count == 0:
            request.setResponseCode(http.NOT_FOUND)
            returnValue({})

        request.setResponseCode(http.OK)
        returnValue(props)

    @handler('/users/<string:user_id>/', methods=['DELETE'])
    @inlineCallbacks
    def delete_user(self, request, user_id):
        response = yield cypher_query(
            "MATCH (n:User {user_id: {user_id}}) "
            "OPTIONAL MATCH (n)-[r]-() "
            "DELETE n,r "
            "RETURN count(n) AS COUNT", {
                "user_id": user_id,
            })
        content = yield treq.content(response)
        if not http_ok(response):
            raise UserServiceError(content)

        response = json.loads(content)
        count = get_neo4j_data(response)
        if count == 0:
            request.setResponseCode(http.NOT_FOUND)
        else:
            request.setResponseCode(http.NO_CONTENT)
        returnValue({})
