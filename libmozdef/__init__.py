#!/usr/bin/env python

import socket
import os
import sys
from datetime import datetime
import logging
from libmozdef.pathway import Logging
from libmozdef.validate import MozDefValidator

MESSAGE_FIELDS = [
    'source',
    'hostname',
    'category',
    'processid',
    'processname',
    'tags',
    'summary',
    'severity',
    'details',
    'timestamp',
    'utctimestamp'
]


class MozDefMessage(dict):
    # Allow accessing dict elements as object attributes
    # For example : Instead of message['summary'] using message.summary
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self,
                 summary,
                 source,
                 hostname=socket.getfqdn(),
                 severity='INFO',
                 category='event',
                 processid=os.getpid(),
                 processname=sys.argv[0],
                 tags=None,
                 details=None,
                 timestamp=None,
                 utctimestamp=None
                 ):
        """MozDev message object constructor

        :param summary:
        :param source:
        :param hostname:
        :param severity:
        :param category:
        :param processid:
        :param processname:
        :param tags:
        :param details:
        :param timestamp:
        :param utctimestamp:
        """
        super(MozDefMessage, self).__init__()

        if details is None:
            details = {}

        if tags is None:
            tags = []

        # Set the TZ environment variable to work around old Python 2 issues
        # https://stackoverflow.com/q/28573873/168874
        os.environ['TZ'] = 'UTC'
        # If no timestamp is passed use the utctimestamp if it's set, otherwise
        # generate the timestamp
        # If utctimestamp isn't set, leave it blank as MozDef will create a
        # utctimestamp from the timestamp field
        if timestamp is None:
            timestamp = (
                datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')
                if utctimestamp is None else utctimestamp)
        # receivedtimestamp is set by MozDef and shouldn't be sent by the
        # client

        # Additional fields beyond the required should not be in the root of a
        # MozDef message. They should be under the `details` field.

        # Override systems with incorrectly set hostname
        if hostname == 'localhost.localdomain':
            hostname = socket.gethostname()

        # The source field will be ignored. See
        # https://github.com/mozilla/MozDef/issues/623

        # For each argument passed into this __init__ method (locals()) that is
        # in the MESSAGE_FIELDS list of field names and is not None, create an
        # element
        for field in set(MESSAGE_FIELDS) & set(locals()):
            if locals()[field] is not None:
                self[field] = locals()[field]

    def send(self, pathway=None, validator=None):
        """Send the message to MozDef via the `pathway` object's send
        method after validating with the `validator`'s `validate` method.

        :param pathway: A pathway object with a send method
        :param validator: A validator object with a validate method
        :return: The
        """
        if pathway is None:
            pathway = Logging(log_level=logging.WARNING)
        if validator is None:
            validator = MozDefValidator(self.message)
        validator.validate()
        return pathway.send(self)
