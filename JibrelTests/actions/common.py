import json
import requests


class ServiceCodes(object):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404
    SERVICE_ERROR = 500


class Methods(object):
    DELETE = "DELETE"
    GET = "GET"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"



"""
how we can validate data by external framework
1) https://pypi.org/project/flask-expects-json/
2) https://python-jsonschema.readthedocs.io/en/latest/validate/
3) https://marshmallow.readthedocs.io/en/latest/
4) https://richardtier.com/2014/03/24/json-schema-validation-with-django-rest-framework/
"""


def filter_dict_from_none(dict_to_filter):
    return {key: value for key, value in dict_to_filter.items() if value is not None}


class TestService(object):

    def __init__(self, client_api):
        self.client = client_api

    def get_account_balance(self, addresses):
        uri = "/v1/accounts/balances"
        body = {}
        uri_params = {}
        query_params = {"addresses": addresses}
        return self.client.get(uri, body, uri_params, query_params)

    # Full example
    # def test_handle(self, test_uri, test_body_1, test_body_2, query_str):
    #     uri = "/v1/transactions"
    #     body = {
    #         'test_body_1': test_body_1,
    #         'test_body_2': test_body_2,
    #     }
    #     uri_params = {
    #         "test_uri": test_uri,
    #     }
    #     query_params = {
    #         'query_str': query_str
    #     }
    #     return self.client.get(uri, body, uri_params, query_params)



class ClientApi(object):

    def __init__(self, base_url): #maybe need add arg - additional headers
        self.service_link = base_url
        self.headers = {'Content-Type': 'application/json'}

    def _format_uri(self, uri, uri_params, query_params):
        return 'full_url_with_uri_params'

    def _format_body(self, body):
        return {}

    def _format_res(self, resp, json): pass

    def _message(self, *messages): pass # print in console + collect log for report

    def _request(self, type_request, uri, data, auth=None, verify=False):
        self.messages = []
        headers = {k: v for k, v in self.headers.items() if v is not None}
        self._message("%s to the service: %s" % (type_request.upper(), uri))
        self._message("Step: %s to the service: %s" % (type_request.upper(), uri))
        self._message("headers of request:", headers)
        self._message("body of request:", data)
        method_request = getattr(requests, type_request.lower())
        if type_request in (Methods.POST, Methods.PUT, Methods.DELETE, Methods.PATCH):
            resp = method_request(uri, data=data, headers=headers, verify=verify, auth=auth)
        elif type_request == Methods.GET:
            resp = method_request(uri, headers=headers, verify=verify, auth=auth)
        else:
            raise Exception("Unknown type_request %s" % type_request)
        self._message("Service code: %s" % resp.status_code)
        try:
            json_resp = resp.json()
            self._message("response:\n", json.dumps(json_resp, indent=4), '\n')
            res = self._format_res(resp, json_resp)
        except ValueError:
            self._message("[CANT SERIALIZE] response:\n", resp.text, '\n')
            res = self._format_res(resp, resp.text)
        #action for insert message in report file, looks like type_request + ' request ' + self.messages
        del self.messages[:]
        return res

    def post(self, uri, body, uri_params, query_params, headers):
        uri = self._format_uri(uri, uri_params, query_params)
        data = self._format_body(body)
        return self._request(Methods.POST, uri, data, headers)

    def get(self, uri, body, uri_params, query_params):
        uri = self._format_uri(uri, uri_params, query_params)
        return self._request(Methods.GET, uri, "")

    def put(self, uri, body, uri_params, query_params, headers):
        uri = self._format_uri(uri, uri_params, query_params)
        data = self._format_body(body)
        return self._request(Methods.PUT, uri, data, headers)

    def patch(self, uri, body, uri_params, query_params):
        uri = self._format_uri(uri, uri_params, query_params)
        data = self._format_body(body)
        return self._request(Methods.PATCH, uri, data)

    def delete(self, uri, body, uri_params, query_params):
        uri = self._format_uri(uri, uri_params, query_params)
        data = self._format_body(body)
        return self._request(Methods.DELETE, uri, data)

