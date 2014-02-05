# -*- test-case-name: archer.users.tests.test_api -*-

import json
from uuid import uuid4

from twisted.internet.defer import inlineCallbacks, returnValue

import treq

from aludel.service import service, handler, get_json_params, APIError

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
    return 200 <= response.code < 300


def neo4j_data(json_payload):
    neo4j_data = json_payload['data'][0][0]
    return neo4j_data['data']


class UserServiceError(APIError):

    def __init__(self, db_response):
        super(UserServiceError, self).__init__(
            message='DB returned: %s' % (db_response.code,))


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
            "CREATE (user:User { props }) RETURN user", {
                "props": props
            })
        # TODO: Figure out why the content needs to be read.
        #       Something in treq blocks on this.
        yield treq.content(response)
        if not http_ok(response):
            raise UserServiceError(response)

        request.redirect('/users/%s/' % (uuid,))
        returnValue({})

    @handler('/users/<string:user_id>/', methods=['GET'])
    @inlineCallbacks
    def get_user(self, request, user_id):
        response = yield cypher_query(
            "MATCH (user:User {user_id: {user_id}}) return user", {
                "user_id": user_id,
            })
        content = json.loads((yield treq.content(response)))
        returnValue(neo4j_data(content))