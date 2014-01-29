from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.web import server

from archer import comments


class Options(usage.Options):
    optParameters = [
        ["port", "p", 9889, "The port to listen on."]
    ]

class ServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "comments"
    description = "Archer comments service"
    options = Options
    def makeService(self, options):
        return internet.TCPServer(
            int(options['port']),
            server.Site(comments.ServiceRoot())
        )

serviceMaker = ServiceMaker()
