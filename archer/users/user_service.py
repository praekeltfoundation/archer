# -*- test-case-name: archer.users.tests.test_user_service -*-

from twisted.application import strports
from twisted.internet import reactor
from twisted.python import usage
from twisted.web import server

from archer.users.api import UserServiceApp


DEFAULT_PORT = 'tcp:8080'


class Options(usage.Options):
    """Command line args when run as a twistd plugin"""
    # TODO other args
    optParameters = [["endpoint", "e", DEFAULT_PORT,
                      "Port number for airtime-service to listen on"],
                     ["database-connection-string", "d", None,
                      "Database connection string"]]

    def postOptions(self):
        if self['database-connection-string'] is None:
            raise usage.UsageError(
                "--database-connection-string parameter is mandatory.")


def makeService(options):
    app = UserServiceApp(
        options['database-connection-string'], reactor=reactor, pool=None)
    site = server.Site(app.app.resource())
    return strports.service(options['endpoint'], site)
