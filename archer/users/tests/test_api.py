from datetime import datetime
from hashlib import md5
from itertools import izip_longest
import json
from urllib import urlencode
from StringIO import StringIO

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase
from twisted.web.client import Agent, FileBodyProducer, readBody
from twisted.web.http_headers import Headers
from twisted.web.server import Site

from archer.users.api import UserServiceApp


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
        self.user_service = UserServiceApp("sqlite://", reactor=reactor)
        site = Site(self.user_service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        self.client = ApiClient('http://localhost:%s' % (self.listener_port,))

    def tearDown(self):
        return self.listener.loseConnection()

    @inlineCallbacks
    def test_request(self):
        resp = yield self.client.put_json('/', {}, 200)
        self.assertEqual(resp['content'], 'hello world')
