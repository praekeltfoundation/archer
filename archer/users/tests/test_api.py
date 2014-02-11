import json

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial.unittest import TestCase
from twisted.web.client import HTTPConnectionPool
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
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.user_service = UserServiceApp(
            NEO4J_URL, reactor=reactor, pool=self.pool)
        site = Site(self.user_service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        self.addCleanup(self.listener.loseConnection)
        self.addCleanup(self.clear_neo4j)
        self.addCleanup(self.pool.closeCachedConnections)

    def make_url(self, *paths):
        return 'http://localhost:%s/users/%s' % (
            self.listener_port, ('/'.join(map(str, paths)) + '/'
                                 if paths else ''))

    def make_user(self, data):
        """returns the data of the newly created user, including uuid"""
        d = self.create_user(data)
        d.addCallback(lambda resp: resp.headers.getRawHeaders('location')[0])
        d.addCallback(
            lambda location: treq.get('http://localhost:%s%s' % (
                self.listener_port, location), pool=self.pool))
        d.addCallback(lambda resp: treq.json_content(resp))
        return d

    def create_user(self, data):
        """returns the raw response"""
        return treq.post(self.make_url(),
                         data=json.dumps(data),
                         allow_redirects=False,
                         pool=self.pool)

    def update_user(self, uuid, data):
        return treq.put(self.make_url(uuid),
                        data=json.dumps(data),
                        allow_redirects=False,
                        pool=self.pool)

    def get_user(self, uuid):
        return treq.get(self.make_url(uuid), pool=self.pool)

    def delete_user(self, uuid):
        return treq.delete(self.make_url(uuid), pool=self.pool)

    @inlineCallbacks
    def clear_neo4j(self):
        clear_command = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            DELETE n,r
        """
        response = yield cypher_query(clear_command, pool=self.pool)
        yield treq.content(response)
        returnValue(response)

    @inlineCallbacks
    def test_create_user_simple(self):
        payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        resp = yield self.create_user(payload)
        self.assertEqual(resp.code, 302)
        [location] = resp.headers.getRawHeaders('location')
        self.assertTrue(location.startswith('/users/'))

    @inlineCallbacks
    def test_get_user_200(self):
        payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        user = yield self.make_user(payload)
        resp = yield self.get_user(user['user_id'])
        content = yield treq.json_content(resp)
        expected_response = payload.copy()
        expected_response['request_id'] = None
        expected_response['user_id'] = user['user_id']
        self.assertEqual(content, expected_response)

    @inlineCallbacks
    def test_get_user_404(self):
        resp = yield self.get_user('foo')
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
        user = yield self.make_user(payload)
        resp = yield self.delete_user(user['user_id'])
        yield treq.content(resp)
        self.assertEqual(resp.code, http.NO_CONTENT)

    @inlineCallbacks
    def test_delete_user_404(self):
        resp = yield self.delete_user('foo')
        yield treq.content(resp)
        self.assertEqual(resp.code, http.NOT_FOUND)

    @inlineCallbacks
    def test_update_user_200(self):
        original_payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        user = yield self.make_user(original_payload)

        updated_payload = {
            'username': 'username',
            'email_address': 'email@address.com',
            'msisdn': '+27000000001',
        }
        resp = yield self.update_user(user['user_id'], updated_payload)
        content = yield treq.content(resp)
        self.assertEqual(resp.code, http.OK)
        expected_response = {
            'user_id': user['user_id'],
            'request_id': None,
        }
        expected_response.update(updated_payload)
        self.assertEqual(json.loads(content), expected_response)

    @inlineCallbacks
    def test_update_user_404(self):
        payload = {
            'username': 'username',
            'email_address': 'email@address.com',
            'msisdn': '+27000000001',
        }
        resp = yield self.update_user('foo', payload)
        yield treq.content(resp)
        self.assertEqual(resp.code, http.NOT_FOUND)

    # @inlineCallbacks
    # def test_create_relationship(self):
    #     payload = {
    #         'username': 'username',
    #         'username':
    #     }