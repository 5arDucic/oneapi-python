# -*- coding: utf-8 -*-

import pdb

import json as mod_json
import logging as mod_logging

import requests as mod_requests

import models as mod_models
import object as mod_object
import utils as mod_utils

DEFAULT_BASE_URL = 'http://api.parseco.com'

class AbstractOneApiClient:
    """
    Note that this is *not* a http session. This class is just a utility class 
    holding authorization data and a few utility methods for http requests.
    """

    def __init__(self, username, password, base_url=None):
        self.base_url = base_url if base_url else DEFAULT_BASE_URL
        self.username = username
        self.password = password

        if not self.base_url.endswith('/'):
            self.base_url += '/'

    def get_client_correlator(self, client_correlator=None):
        if client_correlator:
            return client_correlator;

        return mod_utils.get_random_alphanumeric_string()

    def get_rest_url(self, rest_path):
        if not rest_path:
            return self.base_url

        if rest_path.startswith('/'):
            return self.base_url + rest_path[1:]

        return self.base_url + rest_path

    def get_exception_details(self, exception_response):
        """ Returns message_id, text and variables from the standard API exception response. """
        exception = None
        try:
            exception = result['requestError']['serviceException']
        except Exception, e:
            pass
        if not exception:
            try:
                exception = result['requestError']['serviceException']
            except Exception, e:
                pass
        message_id = exception['messageId'] if exception.has_key('messageId') else None
        text = exception['text'] if exception.has_key('text') else None
        variables = exception['variables'] if exception.has_key('variables') else None

        return message_id, text, variables

    def execute_GET(self, rest_path, params=None, leave_undecoded=None):
        response = mod_requests.get(self.get_rest_url(rest_path), params=params, auth=(self.username, self.password))

        mod_logging.debug('status code:{0}'.format(response.status_code))
        mod_logging.debug('text:{0}'.format(response.text))
        mod_logging.debug('content:{0}'.format(response.content))

        is_success = 200 <= response.status_code <= 299

        if leave_undecoded:
            return is_success, response.content

        return is_success, mod_json.loads(response.content)

    def execute_POST(self, rest_path, params=None, leave_undecoded=None):
        response = mod_requests.post(self.get_rest_url(rest_path), data=params, auth=(self.username, self.password))

        mod_logging.debug('status code:{0}'.format(response.status_code))
        mod_logging.debug('params: {0}'.format(params))
        mod_logging.debug('text:{0}'.format(response.text))
        mod_logging.debug('content:{0}'.format(response.content))

        is_success = 200 <= response.status_code <= 299

        if leave_undecoded:
            return is_success, response.content

        return is_success, mod_json.loads(response.content)

    def execute_DELETE(self, rest_path, params=None, leave_undecoded=None):
        response = mod_requests.delete(self.get_rest_url(rest_path), data=params, auth=(self.username, self.password))

        mod_logging.debug('status code:{0}'.format(response.status_code))
        mod_logging.debug('text:{0}'.format(response.text))
        mod_logging.debug('content:{0}'.format(response.content))

        if leave_undecoded:
            return is_success, response.content

        return is_success, mod_json.loads(response.content)

class SmsClient(AbstractOneApiClient):

    def __init__(self, username, password, base_url=None):
        AbstractOneApiClient.__init__(self, username, password, base_url=base_url)

    def send_sms(self, sms):
        client_correlator = sms.client_correlator
        if not client_correlator:
            client_correlator = mod_utils.get_random_alphanumeric_string()

        params = {
            'senderAddress': sms.sender_address,
            'address': sms.address,
            'message': sms.message,
            'clientCorrelator': client_correlator,
            'senderName': 'tel:{0}'.format(sms.sender_address),
        }

        if sms.notify_url:
            params['notifyURL'] = sms.notify_url
        if sms.callback_data:
            params['callbackData'] = sms.callback_data

        is_success, result = self.execute_POST(
                '/1/smsmessaging/outbound/{0}/requests'.format(sms.sender_address),
                params = params
        )

        return mod_object.Conversions.from_json(mod_models.ResourceReference, result, not is_success)

    def query_delivery_status(self, client_correlator_or_resource_reference):
        if hasattr(client_correlator_or_resource_reference, 'client_correlator'):
            client_correlator = client_correlator_or_resource_reference.client_correlator
        else:
            client_correlator = client_correlator_or_resource_reference

        client_correlator = self.get_client_correlator(client_correlator)

        params = {
            'clientCorrelator': client_correlator,
        }

        is_success, result = self.execute_GET(
                '/1/smsmessaging/outbound/TODO/requests/{0}/deliveryInfos'.format(client_correlator),
                params = params
        )

        return mod_object.Conversions.from_json(mod_models.DeliveryInfoList, result, not is_success)

