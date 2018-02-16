
from collections import namedtuple

FSMTrace = namedtuple('FSMTrace', ['order', 'fsm_name', 'fsm_id', 'from_state', 'to_state', 'message_type'])
ChannelTrace = namedtuple('ChannelTrace', ['order', 'from_fsm', 'to_fsm', 'sent_message_type'])
