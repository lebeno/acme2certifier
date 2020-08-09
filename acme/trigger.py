#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Challenge class """
from __future__ import print_function
import json
import importlib
from acme.certificate import Certificate
from acme.db_handler import DBstore
from acme.helper import convert_byte_to_string, cert_pubkey_get, csr_pubkey_get, cert_der2pem, b64_decode, load_config, ca_handler_get

class Trigger(object):
    """ Challenge handler """

    def __init__(self, debug=None, srv_name=None, logger=None):
        self.debug = debug
        self.server_name = srv_name
        self.cahandler = None
        self.logger = logger
        self.dbstore = DBstore(debug, self.logger)
        self.tnauthlist_support = False

    def __enter__(self):
        """ Makes ACMEHandler a Context Manager """
        self._config_load()
        return self

    def __exit__(self, *args):
        """ close the connection at the end of the context """

    def _certname_lookup(self, cert_pem):
        """ compared certificate against csr stored in db """
        self.logger.debug('Trigger._certname_lookup()')

        result_list = []
        # extract the public key form certificate
        cert_pubkey = cert_pubkey_get(self.logger, cert_pem)
        with Certificate(self.debug, 'foo', self.logger) as certificate:
            # search certificates in status "processing"
            cert_list = certificate.certlist_search('order__status_id', 4, ('name', 'csr', 'order__name'))

            for cert in cert_list:
                # extract public key from certificate and compare it with pub from cert
                if 'csr' in cert:
                    if cert['csr']:
                        csr_pubkey = csr_pubkey_get(self.logger, cert['csr'])
                        if csr_pubkey == cert_pubkey:
                            result_list.append({'cert_name': cert['name'], 'order_name': cert['order__name']})
        self.logger.debug('Trigger._certname_lookup() ended with: {0}'.format(result_list))

        return result_list

    def _config_load(self):
        """" load config from file """
        self.logger.debug('Certificate._config_load()')
        config_dic = load_config()
        if 'Order' in config_dic:
            self.tnauthlist_support = config_dic.getboolean('Order', 'tnauthlist_support', fallback=False)
        if 'CAhandler' in config_dic and 'handler_file' in config_dic['CAhandler']:
            try:
                ca_handler_module = importlib.import_module(ca_handler_get(self.logger, config_dic['CAhandler']['handler_file']))
            except BaseException:
                ca_handler_module = importlib.import_module('acme.ca_handler')
        else:
            ca_handler_module = importlib.import_module('acme.ca_handler')
        self.logger.debug('ca_handler: {0}'.format(ca_handler_module))
        # store handler in variable
        self.cahandler = ca_handler_module.CAhandler

    def _payload_process(self, payload):
        """ process payload """
        self.logger.debug('Trigger._payload_process()')
        with self.cahandler(self.debug, self.logger) as ca_handler:
            if payload:
                (error, cert_bundle, cert_raw) = ca_handler.trigger(payload)
                if cert_bundle and cert_raw:
                    # returned cert_raw is in dear format, convert to pem to lookup the pubic key
                    cert_pem = convert_byte_to_string(cert_der2pem(b64_decode(self.logger, cert_raw)))

                    # lookup certificate_name by comparing public keys
                    cert_name_list = self._certname_lookup(cert_pem)

                    if cert_name_list:
                        for cert in cert_name_list:
                            data_dic = {'cert' : cert_bundle, 'name': cert['cert_name'], 'cert_raw' : cert_raw}
                            try:
                                self.dbstore.certificate_add(data_dic)
                            except BaseException as err_:
                                self.logger.critical('acme2certifier database error in trigger._payload_process() add: {0}'.format(err_))
                            if 'order_name' in cert and cert['order_name']:
                                try:
                                    # update order status to 5 (valid)
                                    self.dbstore.order_update({'name': cert['order_name'], 'status': 'valid'})
                                except BaseException as err_:
                                    self.logger.critical('acme2certifier database error in trigger._payload_process() upd: {0}'.format(err_))
                        code = 200
                        message = 'OK'
                        detail = None
                    else:
                        code = 400
                        message = 'certificate_name lookup failed'
                        detail = None
                else:
                    code = 400
                    message = error
                    detail = None
            else:
                code = 400
                message = 'payload malformed'
                detail = None

        self.logger.debug('Trigger._payload_process() ended with: {0} {1}'.format(code, message))
        return (code, message, detail)

    def parse(self, content):
        """ new oder request """
        self.logger.debug('Trigger.parse()')

        # convert to json structure
        try:
            payload = json.loads(convert_byte_to_string(content))
        except BaseException:
            payload = {}

        if 'payload' in payload:
            if payload['payload']:
                (code, message, detail) = self._payload_process(payload['payload'])
            else:
                code = 400
                message = 'malformed'
                detail = 'payload empty'
        else:
            code = 400
            message = 'malformed'
            detail = 'payload missing'
        response_dic = {}
        # check message


        # prepare/enrich response
        response_dic['header'] = {}
        response_dic['code'] = code
        response_dic['data'] = {'status': code, 'message': message}
        if detail:
            response_dic['data']['detail'] = detail

        self.logger.debug('Trigger.parse() returns: {0}'.format(json.dumps(response_dic)))
        return response_dic
