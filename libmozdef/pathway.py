#!/usr/bin/env python

import json
import logging
try:
    import boto3
    import botocore.exceptions
    import botocore.parsers
    from requests_futures.sessions import FuturesSession
except ImportError:
    boto3 = None
    botocore = None
    FuturesSession = None


class Stdout(object):
    def __init__(self, prefix=''):
        self.prefix = prefix

    def send(self, message):
        if self.prefix:
            print(self.prefix)
        print(json.dumps(message, indent=4))


class Logging(object):
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger(__name__)
        self.log_level = log_level

    def send(self, message):
        message = json.dumps(message)
        logging.log(self.log_level, message)
        return True


class AWSMessagingService(object):
    MAX_MESSAGE_SIZE = 256 * 1024

    def __init__(self):
        try:
            boto3.__name__
        except NameError:
            raise ImportError(
                'boto3 not loaded. Run pip install libmozdef[aws]')

    def get_message_body(self, message):
        message_body = json.dumps(message)
        # TODO : This won't be accurate in python 2 since message_body won't be
        # unicode and the size limit is in bytes not characters
        assert len(message_body) <= self.MAX_MESSAGE_SIZE, (
                'message length of %s is over the maximum allowed message '
                'size of %s' % (len(message_body), self.MAX_MESSAGE_SIZE))
        return message_body


class SQS(AWSMessagingService):
    def __init__(self,
                 queue_name,
                 aws_account_id=None,
                 region=None):
        super(SQS, self).__init__()
        self.queue_name = queue_name
        self.aws_account_id = aws_account_id
        # If no region is set, assume the queue is in the local region
        self.region = (
            region if region is not None
            else boto3.session.Session().region_name)
        assert self.region is not None, (
            'AWS region is unset, unable to connect to SQS queue')

    def send(self, message):
        sqs = boto3.resource('sqs', self.region)

        if self.aws_account_id is not None:
            queue = sqs.get_queue_by_name(
                QueueName=self.queue_name,
                QueueOwnerAWSAccountId=self.aws_account_id)
        else:
            queue = sqs.get_queue_by_name(QueueName=self.queue_name)

        message_body = self.get_message_body(message)
        try:
            response = queue.send_message(MessageBody=message_body)
        except (botocore.exceptions.ClientError,
                botocore.parsers.ResponseParserError) as e:
            raise Exception(
                'message failed to send to SQS due to %s' % e)
        return response


class SNS(AWSMessagingService):
    def __init__(self,
                 topic_arn):
        super(SNS, self).__init__()
        self.topic_arn = topic_arn

    def send(self, message):
        client = boto3.client('sns')
        message_body = self.get_message_body(message)
        try:
            response = client.publish(
                TopicArn=self.topic_arn,
                Message=message_body)
        except (botocore.exceptions.ClientError,
                botocore.parsers.ResponseParserError) as e:
            raise Exception(
                'message failed to send to SNS due to %s' % e)
        return response


class HTTP(object):
    def __init__(self,
                 url,
                 verify_cert=True,
                 block_on_response=False,
                 buffer_size=1):
        try:
            self.session = FuturesSession()
        except TypeError:
            raise ImportError(
                'requests-futures not loaded. Run pip install libmozdef[http]')
        self.url = url
        self.session.trust_env = False
        self.session.verify = verify_cert
        self.block_on_response = block_on_response
        self.buffer_size = buffer_size
        self.message_buffer = []

    def __enter__(self):
        """Enter the HTTP runtime context

        :return:
        """
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Exit the runtime context by bulk sending the remaining messages in
        the message_buffer

        :param exception_type:
        :param exception_value:
        :param traceback:
        :return:
        """
        if self.buffer_size > 1 and len(self.message_buffer) > 0:
            self.bulk_send()

    def bulk_send(self):
        """Send a newline delimited list of json documents from message_buffer
        to the MozDef _bulk/ endpoint

        :return:
        """
        # https://github.com/mozilla/MozDef/blob/fc3d8cef43/loginput/index.py#L48
        future_response = self.session.post(
            self.url,
            data='\n'.join([json.dumps(x) for x in self.message_buffer]))
        del self.message_buffer[:]
        if not self.block_on_response:
            return True
        result = future_response.result()
        assert result.status_code == 200, (
                'POST to %s returned %s status code'
                % (self.url, result.status_code))
        return result

    def send(self, message):
        """Send message to url or if buffer_size is set, buffer messages until
        the buffer exceeds the buffer_size and then flush them by calling
        bulk_send

        :param message:
        :return:
        """
        if self.buffer_size > 1:
            self.message_buffer.append(message)
            if len(self.message_buffer) > self.buffer_size:
                return self.bulk_send()
            else:
                return 'Message buffered'
        else:
            future_response = self.session.post(
                self.url,
                json=message)
            if not self.block_on_response:
                return True
            result = future_response.result()
            assert result.status_code == 200, (
                    'POST to %s returned %s status code' % (self.url,
                                                            result.status_code))
            return result
