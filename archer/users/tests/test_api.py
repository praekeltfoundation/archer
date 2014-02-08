import json

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial.unittest import TestCase
from twisted.web.server import Site
from twisted.web import http

import treq
from treq._utils import get_global_pool

from archer.users.api import UserServiceApp, NEO4J_URL, cypher_query

from twisted.internet.base import DelayedCall
DelayedCall.debug = True


class TestUserServiceApp(TestCase):

    timeout = 1

    def setUp(self):
        self.patch(UserServiceApp, 'make_uuid', lambda _: 'uuid')
        self.user_service = UserServiceApp(NEO4J_URL, reactor=reactor)
        site = Site(self.user_service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
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
    def test_get_user_200(self):
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

    @inlineCallbacks
    def test_get_user_404(self):
        resp = yield treq.get(self.mk_url('uuid'))
        content = json.loads((yield treq.content(resp)))
        self.assertEqual(resp.code, http.NOT_FOUND)
        self.assertEqual(content, {
            'request_id': None
        })

    @inlineCallbacks
    def test_delete_user_204(self):
        payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        yield self.mk_user(payload)

        resp = yield treq.delete(self.mk_url('uuid'))
        yield treq.content(resp)
        self.assertEqual(resp.code, http.NO_CONTENT)

    @inlineCallbacks
    def test_delete_user_404(self):
        resp = yield treq.delete(self.mk_url('uuid'))
        yield treq.content(resp)
        self.assertEqual(resp.code, http.NOT_FOUND)
