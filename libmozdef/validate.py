#!/usr/bin/env python


class MozDefValidator(object):
    def __init__(self, message):
        self.message = message

    def validate(self):
        assert self.message['summary'] != '', 'summary is empty'
        assert self.message['summary'] is not None, 'summary is None'
        severity_levels = ['INFO', 'WARNING', 'CRITICAL', 'ERROR', 'DEBUG']
        assert self.message['severity'] in severity_levels, (
            'severity %s is not allowed %s' % (self.message['severity'],
                                               severity_levels))


class MozDefExampleValidator(MozDefValidator):
    def validate(self):
        super(MozDefExampleValidator, self).validate()
        assert 'example' in self.message['details'], (
            'example key missing from details')
