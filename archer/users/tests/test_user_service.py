from twisted.python.usage import UsageError
from twisted.trial.unittest import TestCase

from archer.users import user_service


class TestUserService(TestCase):
    def test_make_service(self):
        svc = user_service.makeService({
            'database-connection-string': 'neo4j://',
            'endpoint': 'tcp:0',
        })
        assert not svc.running

    def test_happy_options(self):
        opts = user_service.Options()
        opts.parseOptions(['-e', 'tcp:1234', '-d', 'neo4j://'])
        assert set(opts.keys()) == set([
            'endpoint', 'database-connection-string'])
        assert opts['database-connection-string'] == 'neo4j://'
        assert opts['endpoint'] == 'tcp:1234'

    def test_default_port(self):
        opts = user_service.Options()
        opts.parseOptions(['-d', 'neo4j://'])
        assert set(opts.keys()) == set([
            'endpoint', 'database-connection-string'])
        assert opts['database-connection-string'] == 'neo4j://'
        assert opts['endpoint'] == 'tcp:8080'

    def test_db_conn_str_required(self):
        opts = user_service.Options()
        self.assertRaises(UsageError, opts.parseOptions, [])
