import unittest
from libmozdef import MozDefMessage
from libmozdef.pathway import Stdout
from libmozdef.validate import MozDefValidator
from libmozdef.validate import MozDefExampleValidator


class TestLibMozdef(unittest.TestCase):
    def setUp(self):
        self.message = MozDefMessage(
            summary='john login attempts over threshold, account locked',
            source='/var/log/syslog/2014.01.02.log')

    def test_message_creation(self):
        # Message fields have defaults
        self.assertEqual(self.message['severity'], 'INFO')

        # Message fields can be set by attribute
        self.message.severity = 'DEBUG'
        self.assertEqual(self.message['severity'], 'DEBUG')

        # Message fields can be set as a dictionary element
        self.message['tags'] = ['foo', 'bar']
        self.assertEqual(self.message.tags, ['foo', 'bar'])

    def test_validation(self):
        try:
            # Optionally validate the message
            validator = MozDefValidator(self.message)
            validator.validate()
        except AssertionError:
            self.fail('Validation failed despite the message being a valid '
                      'MozDef message')
        # An AssertionError is raised when validation fails
        with self.assertRaises(AssertionError):
            self.message.summary = ''
            validator = MozDefValidator(self.message)
            validator.validate()

    def test_example_validation(self):
        # MozDefExampleValidator illustrates how to create additional
        # validation logic for specific message types
        with self.assertRaises(AssertionError):
            validator = MozDefExampleValidator(self.message)
            validator.validate()

        try:
            self.message.details['example'] = 'foo'
            validator = MozDefExampleValidator(self.message)
            validator.validate()
        except AssertionError:
            self.fail('Example validation with MozDefExampleValidator failed '
                      'despite having an "example" key in "details"')

    def test_send_stdout(self):
        # The Stdout pathway prints the message to stdout
        destination = Stdout()
        # Send the message
        self.message.send(destination=destination)

        # The Stdout pathway can accept a prefix argument as an illustration
        # of how pathways can take arguments
        destination = Stdout(prefix='Here is my message')
        # Send the message
        self.message.send(destination=destination)


if __name__ == '__main__':
    unittest.main()
