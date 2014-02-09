import json
import urllib

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

    timeout = 5

    def setUp(self):
        self.patch(UserServiceApp, 'make_uuid', lambda _: 'uuid')
        self.user_service = UserServiceApp(NEO4J_URL, reactor=reactor)
        site = Site(self.user_service.app.resource())
        self.listener = reactor.listenTCP(0, site, interface='localhost')
        self.listener_port = self.listener.getHost().port
        self.addCleanup(self.listener.loseConnection)
        self.addCleanup(self.clear_neo4j)

    def make_url(self, *paths):
        return 'http://localhost:%s/users/%s' % (
            self.listener_port, ('/'.join(paths) + '/' if paths else ''))

    def create_user(self, data):
        return treq.post(self.make_url(),
                         data=json.dumps(data),
                         allow_redirects=False)

    def update_user(self, uuid, data):
        return treq.put(self.make_url(uuid),
                        data=json.dumps(data),
                        allow_redirects=False)

    def get_user(self, uuid):
        return treq.get(self.make_url(uuid))

    def delete_user(self, uuid):
        return treq.delete(self.make_url(uuid))

    def query_user(self, **kwargs):
        url = '%s?%s' % (self.make_url(), urllib.urlencode(kwargs))
        return treq.get(url)

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
        resp = yield self.create_user(payload)
        self.assertEqual(resp.code, 302)
        self.assertEqual(
            resp.headers.getRawHeaders('location'),
            ['/users/uuid/'])

    @inlineCallbacks
    def test_user_query(self):
        payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        yield self.create_user(payload)
        resp = yield self.query_user(
            username='foo', email_address='foo@bar.com',
            msisdn='+27000000000')
        content = json.loads((yield treq.content(resp)))
        self.assertEqual(
            content["matches"],
            [{
                'username': 'foo',
                'email_address': 'foo@bar.com',
                'msisdn': '+27000000000',
                'user_id': 'uuid',
            }])

    @inlineCallbacks
    def test_get_user_200(self):
        payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        yield self.create_user(payload)

        resp = yield self.get_user('uuid')
        content = json.loads((yield treq.content(resp)))
        expected_response = payload.copy()
        expected_response['request_id'] = None
        expected_response['user_id'] = 'uuid'
        self.assertEqual(content, expected_response)

    @inlineCallbacks
    def test_get_user_404(self):
        resp = yield self.get_user('uuid')
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
        yield self.create_user(payload)

        resp = yield self.delete_user('uuid')
        yield treq.content(resp)
        self.assertEqual(resp.code, http.NO_CONTENT)

    @inlineCallbacks
    def test_delete_user_404(self):
        resp = yield self.delete_user('uuid')
        yield treq.content(resp)
        self.assertEqual(resp.code, http.NOT_FOUND)

    @inlineCallbacks
    def test_update_user_200(self):
        original_payload = {
            'username': 'foo',
            'email_address': 'foo@bar.com',
            'msisdn': '+27000000000',
        }
        yield self.create_user(original_payload)

        updated_payload = {
            'username': 'username',
            'email_address': 'email@address.com',
            'msisdn': '+27000000001',
        }
        resp = yield self.update_user('uuid', updated_payload)
        content = yield treq.content(resp)
        self.assertEqual(resp.code, http.OK)
        expected_response = {
            'user_id': 'uuid',
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
        resp = yield self.update_user('uuid', payload)
        yield treq.content(resp)
        self.assertEqual(resp.code, http.NOT_FOUND)
