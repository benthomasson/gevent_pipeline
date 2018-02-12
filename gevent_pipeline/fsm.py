

from gevent.queue import Queue

from conf import settings
import messages
import gevent


class _Channel(object):

    def __init__(self, from_fsm, to_fsm, tracer, queue=None):
        if queue is None:
            self.queue = Queue()
        else:
            self.queue = queue
        self.from_fsm = from_fsm
        self.to_fsm = to_fsm
        self.tracer = tracer

    def put(self, item):
        self.tracer.send_trace_message(messages.ChannelTrace(self.from_fsm.name,
                                                             self.to_fsm.name,
                                                             item.__class__.__name__))
        self.queue.put(item)

    def get(self, block=True, timeout=None):
        return self.queue.get(block, timeout)

    receive = get


def Channel(from_fsm, to_fsm, tracer, queue=None):
    if settings.instrumented:
        return _Channel(from_fsm, to_fsm, tracer, queue)
    if queue is not None:
        return queue
    else:
        return Queue()


class _NullChannel(object):

    def __init__(self):
        pass

    def put(self, item):
        pass

NullChannelSingleton = _NullChannel()


class _NullChannelInstrumented(object):

    def __init__(self, from_fsm, tracer):
        self.from_fsm = from_fsm
        self.tracer = tracer

    def put(self, item):
        self.tracer.send_trace_message(messages.ChannelTrace(self.from_fsm.name,
                                                             None,
                                                             item.__class__.__name__))


def NullChannel(from_fsm, tracer):

    if settings.instrumented:
        return _NullChannelInstrumented(from_fsm, tracer)
    else:
        return NullChannelSingleton


class FSMController(object):

    def __init__(self, context, name, initial_state, tracer):
        self.context = context
        self.name = name
        self.tracer = tracer
        self.handling_message_type = 'start'
        self.state = initial_state
        self.state.start(self)
        self.handling_message_type = None
        self.inboxes = dict()
        self.outboxes = dict(default=NullChannel(self, tracer))

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
                                                             self.state.__class__.__name__,
                                                             state.__class__.__name__,
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
        self.outboxes.get('default', NullChannelSingleton).put(message)

    def receive_messages(self):

        while True:
            gevent.sleep(0)
            if self.inboxes.get('default', None):
                inbox = self.inboxes.get('default')
                message = inbox.get()
                message_type = message.__class__.__name__
                self.handle_message(message_type, message)
            else:
                break


class State(object):

    def start(self, controller):
        pass

    def end(self, controller):
        pass


def transitions(*args):
    def decorator(fn):
        fn.transitions = args
        return fn
    return decorator
