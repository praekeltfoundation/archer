import json
from pprint import pprint
from urllib import urlencode
from StringIO import StringIO

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial.unittest import TestCase
from twisted.web.client import Agent, FileBodyProducer, readBody
from twisted.web.http_headers import Headers
from twisted.web.server import Site

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

    def put_json(self, url_path, params, expected_code=200):
        headers = Headers({'Content-Type': ['application/json']})
        return self.put(
            url_path, headers, json.dumps(params), expected_code)


class TestUserServiceApp(TestCase):
    timeout = 5

    def setUp(self):
        self.user_service = UserServiceApp(NEO4J_URL, reactor=reactor)
        site = Site(self.user_service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        self.client = ApiClient('http://localhost:%s' % (self.listener_port,))
        self.addCleanup(self.listener.loseConnection)
        self.addCleanup(self.clear_neo4j)

    @inlineCallbacks
    def clear_neo4j(self):
        clear_command = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            DELETE n,r
        """
        body = yield cypher_query(clear_command)
        # NOTE: close the pool's connections
        pool = get_global_pool()
        pool.closeCachedConnections()
        returnValue(body)

    @inlineCallbacks
    def test_create_user_simple(self):
        payload = {
            'username': 'foo',
            'password': 'bar',
            'email': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        resp = yield self.client.put_json('/', payload, 200)
        # NOTE: still figuring out what Neo4J returns
        neo4j_data = resp['data'][0][0]
        self.assertEqual(neo4j_data['data'], payload)
