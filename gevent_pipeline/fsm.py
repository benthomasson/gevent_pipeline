

from gevent.queue import Queue

from conf import settings
import messages


class _Channel(object):

    def __init__(self, from_fsm, to_fsm, tracer):
        self.queue = Queue()
        self.from_fsm = from_fsm
        self.to_fsm = to_fsm
        self.tracer = tracer

    def put(self, item):
        self.queue.put(item)

    def get(self, block=True, timeout=None):
        return self.queue.get(block, timeout)

    receive = get


def Channel(from_fsm, to_fsm, tracer):
    if settings.instrumented:
        return _Channel(from_fsm, to_fsm, tracer)
    else:
        return Queue()


class _NullChannel(object):

    def __init__(self, from_fsm, tracer):
        self.from_fsm = from_fsm

    def put(self, item):
        pass


class _NullChannelInstrumented(object):

    def __init__(self, from_fsm, tracer):
        self.from_fsm = from_fsm
        self.tracer = tracer

    def put(self, item):
        self.tracer.send_trace_message(messages.ChannelTrace(self.from_fsm.name,
                                                             None,
                                                             item[0]))


def NullChannel(from_fsm, tracer):

    if settings.instrumented:
        return _NullChannelInstrumented(from_fsm, tracer)
    else:
        return _NullChannel(from_fsm, tracer)


class FSMController(object):

    def __init__(self, context, name, initial_state, tracer):
        self.context = context
        self.name = name
        self.tracer = tracer
        self.handling_message_type = 'start'
        self.state = initial_state
        self.state.start(self)
        self.handling_message_type = None
        self.inboxes = []
        self.delegate_channel = NullChannel(self, tracer)

    def changeState(self, state):
        if self.state:
            try:
                old_handling_message_type = self.handling_message_type
                self.handling_message_type = 'end'
                self.state.end(self)
            finally:
                self.handling_message_type = old_handling_message_type
        if settings.instrumented:
            self.tracer.send_trace_message(messages.FSMTrace(self.tracer.trace_order_seq(),
                                                             self.name,
                                                             self.state.name,
                                                             state.name,
                                                             self.handling_message_type))
        self.state = state
        if self.state:
            try:
                old_handling_message_type = self.handling_message_type
                self.handling_message_type = 'start'
                self.state.start(self)
            finally:
                self.handling_message_type = old_handling_message_type

    def handle_message(self, message_type, message):
        try:
            old_handling_message_type = self.handling_message_type
            self.handling_message_type = message_type
            handler_name = "on{0}".format(message_type)
            handler = getattr(self.state, handler_name, self.default_handler)
            handler(self, message_type, message)
        finally:
            self.handling_message_type = old_handling_message_type

    def default_handler(self, controller, message_type, message):
        self.delegate_channel.put((message_type, message))

    def receive_messages(self):

        while True:
            for inbox in self.inboxes:
                message_type_and_message = inbox.get()
                message_type = message_type_and_message.pop(0)
                message = message_type_and_message.pop(0)
                self.handle_message(message_type, message)


class State(object):

    def start(self, controller):
        pass

    def end(self, controller):
        pass
