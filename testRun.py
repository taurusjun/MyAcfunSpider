#!/usr/bin/python

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.web.client import Agent
from pprint import pprint

class LoopingStuff (object):

    def cp_process_request(self, return_obj):
        print "In callback"
        pprint (return_obj)

    def cb_process_error(self, return_obj):
        print "In Errorback"
        pprint(return_obj)
        self.loopstopper()

    def send_request(self):
        agent = Agent(reactor)
        req_result = agent.request('GET', 'http://www.baidu.com')
        req_result.addCallbacks(self.cp_process_request, self.cb_process_error)

def main():
    looping_stuff_holder = LoopingStuff()
    list_call = task.LoopingCall(looping_stuff_holder.send_request)
    looping_stuff_holder.loopstopper = list_call.stop
    list_call.start(2)
    reactor.callLater(10, reactor.stop)
    reactor.run()

if __name__ == '__main__':
  main()