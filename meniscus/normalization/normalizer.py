from meniscus.queue import celery
from meniscus.normalization.lognorm import get_normalizer
from meniscus import env
import json


_LOG = env.get_logger(__name__)
_normalizer, loaded_normalizer_rules = get_normalizer()


def should_normalize(message):
    """Returns true only if the pattern is in the loaded rules
    list and there is a string msg in the message dictionary"""
    should_normalize = (
        message['meniscus']['correlation']['pattern'] in
        loaded_normalizer_rules)
    can_normalize = ('msg' in message)
    return should_normalize and can_normalize


@celery.task(acks_late=True, max_retries=None, serializer="json")
def normalize_message(message):
    """Takes a message and normalizes it."""
    message['msg'] = json.loads(
        _normalizer.normalize(message['msg']).as_json())
    return message