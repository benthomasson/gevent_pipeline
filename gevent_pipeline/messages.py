
from collections import namedtuple

FSMTrace = namedtuple('FSMTrace', ['order', 'fsm_name', 'from_state', 'to_state', 'recv_message_type'])
ChannelTrace = namedtuple('ChannelTrace', ['from_fsm', 'to_fsm', 'sent_message_type'])
