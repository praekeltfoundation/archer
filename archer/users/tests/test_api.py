import json
from urllib import urlencode
from StringIO import StringIO

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial.unittest import TestCase
from twisted.web.client import Agent, FileBodyProducer, readBody
from twisted.web.http_headers import Headers
from twisted.web.server import Site

import treq
from treq._utils import get_global_pool

from archer.users.api import UserServiceApp, NEO4J_URL, cypher_query


class ApiClient(object):
    def __init__(self, base_url):
        self._base_url = base_url

    def _make_url(self, url_path):
        return '%s/%s' % (self._base_url, url_path.lstrip('/'))

    def _make_call(self, method, url_path, headers, body, expected_code):
        agent = Agent(reactor)
        url = self._make_url(url_path)
        d = agent.request(method, url, headers, body)
        return d.addCallback(self._get_response_body, expected_code)

    def _get_response_body(self, response, expected_code):
        assert response.code == expected_code
        return readBody(response).addCallback(json.loads)

    def get(self, url_path, params, expected_code):
        url_path = '?'.join([url_path, urlencode(params)])
        return self._make_call('GET', url_path, None, None, expected_code)

    def put(self, url_path, headers, content, expected_code=200):
        body = FileBodyProducer(StringIO(content))
        return self._make_call('PUT', url_path, headers, body, expected_code)

    def put(self, url_path, headers, content, expected_code=200):
        body = FileBodyProducer(StringIO(content))
        return self._make_call('POST', url_path, headers, body, expected_code)

    def put_json(self, url_path, params, expected_code=200):
        headers = Headers({'Content-Type': ['application/json']})
        return self.put(
            url_path, headers, json.dumps(params), expected_code)

    def post_json(self, url_path, params, expected_code=302):
        headers = Headers({'Content-Type': ['application/json']})
        return self.post(
            url_path, headers, json.dumps(params), expected_code)


class TestUserServiceApp(TestCase):

    timeout = 1

    def setUp(self):
        self.patch(UserServiceApp, 'make_uuid', lambda _: 'uuid')
        self.user_service = UserServiceApp(NEO4J_URL, reactor=reactor)
        site = Site(self.user_service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        # self.client = ApiClient(
        #     'http://localhost:%s/users' % (self.listener_port,))
        self.addCleanup(self.listener.loseConnection)
        self.addCleanup(self.clear_neo4j)

    def mk_url(self, *paths):
        return 'http://localhost:%s/users/%s' % (
            self.listener_port, ('/'.join(paths) + '/' if paths else ''))

    def mk_user(self, data):
        return treq.post(self.mk_url(), data=json.dumps(data),
                         allow_redirects=False)

    @inlineCallbacks
    def clear_neo4j(self):
        clear_command = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            DELETE n,r
        """
        response = yield cypher_query(clear_command)
        yield treq.content(response)
        # NOTE: close the pool's connections
        pool = get_global_pool()
        yield pool.closeCachedConnections()
        returnValue(response)

    @inlineCallbacks
    def test_create_user_simple(self):
        payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        resp = yield self.mk_user(payload)
        self.assertEqual(resp.code, 302)
        self.assertEqual(
            resp.headers.getRawHeaders('location'),
            ['/users/uuid/'])

    @inlineCallbacks
    def test_get_user_simple(self):
        payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        yield self.mk_user(payload)

        resp = yield treq.get(self.mk_url('uuid'))
        content = json.loads((yield treq.content(resp)))
        expected_response = payload.copy()
        expected_response['request_id'] = None
        expected_response['user_id'] = 'uuid'
        self.assertEqual(content, expected_response)
