import json
import requests
import logging

from qa_tool.custom_structure import Enum
from qa_tool.libs.reporter import reporter

TIMEOUT_CONNECTION = 10
TIMEOUT_READ = 60 * 5
REQUESTS_TIMEOUT = (TIMEOUT_CONNECTION, TIMEOUT_READ)


class StatusCodes(Enum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    SERVICE_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class Methods(Enum):
    DELETE = "DELETE"
    GET = "GET"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"


def filter_dict_from_none(dict_to_filter):
    return {key: value for key, value in dict_to_filter.items() if value is not None}


def get_params_argv(params):
    return {
        'argvalues': list(params.values()),
        'ids': list(params.keys())
    }


class ClientApi(object):

    def __init__(self, base_url, service_name=None): #maybe need add arg - additional headers
        self.service_link = base_url
        self.service_name = service_name or base_url
        self.headers = {'Content-Type': 'application/json'}
        self._message = []  # TODO: full implement after decide on report tool
        self.api_logger = logging.getLogger(self.service_name)
        self._cookies = {}

    def _format_uri_value_fn(self, data):
        return ','.join(str(i) for i in data) if isinstance(data, (list, set)) else data

    def _get_target_uri(self, uri, query_params):
        if query_params:
            query_params = filter_dict_from_none(query_params)
            query_uri = "&".join(["%s=%s" % (k, self._format_uri_value_fn(v)) for k, v in query_params.items()])
            if query_uri:
                query_uri = "?" + query_uri
            return self.service_link + uri + query_uri
        return self.service_link + uri

    def _format_body(self, body):
        body = body or {}
        if isinstance(body, dict):
            data = filter_dict_from_none(body)
        else:
            data = body
        data = json.dumps(data, indent=4)
        return data

    def _format_res(self, resp, resp_text):
        return resp.status_code, resp_text

    def _report_msg(self, *messages):
        message = ' '.join([str(message) for message in messages])
        print(message)
        self.__messages.append(message)
        self.api_logger.info(message)

    def _update_header_from_cookies(self, resp):
        pass

    def _request(self, type_request, uri, data, headers=None, auth=None, verify=False, **kwargs):
        is_load_file = 'files' in kwargs
        self.__messages = []
        if type_request not in (Methods.GET, Methods.POST, Methods.PUT, Methods.PATCH, Methods.DELETE):
            raise Exception("Unknown request type: %s" % type_request)
        headers = filter_dict_from_none(dict(self.headers, **(headers or {})))
        request_params = dict({
            'headers': headers,
            'verify': verify,
            'auth': auth,
            'cookies': self._cookies,
            'timeout': REQUESTS_TIMEOUT,
        }, **kwargs)
        if is_load_file:
            data = json.loads(data)
        if type_request != Methods.GET:
            request_params.update({'data': data})
        with reporter.step(f"Step: {type_request} to the service: {uri}"):
            method_request = getattr(requests, type_request.lower())
            self._report_msg("Step: %s to the service: %s" % (type_request, uri))
            self._report_msg("headers of request:", headers)
            self._report_msg("body of request:", data)
            resp = method_request(uri, **request_params)
            self._report_msg("Service code: %s" % resp.status_code)
            self._update_header_from_cookies(resp)
            try:
                json_resp = resp.json()
                self._report_msg("response:\n", json.dumps(json_resp, indent=4), '\n')
                res = self._format_res(resp, json_resp)
            except ValueError:
                self._report_msg("[CANT SERIALIZE] response:\n", resp.text, '\n')
                res = self._format_res(resp, resp.text)
            reporter.attach('Request info', '\n'.join(self.__messages))
            del self.__messages[:]
            return res

    def post(self, uri, body=None, query_params=None, headers=None, **kwargs):
        uri = self._get_target_uri(uri, query_params)
        data = self._format_body(body)
        return self._request(Methods.POST, uri, data, headers, **kwargs)

    def get(self, uri, body=None, query_params=None, headers=None):
        uri = self._get_target_uri(uri, query_params)
        return self._request(Methods.GET, uri, "", headers)

    def put(self, uri, body=None, query_params=None, headers=None):
        uri = self._get_target_uri(uri, query_params)
        data = self._format_body(body)
        return self._request(Methods.PUT, uri, data, headers)

    def patch(self, uri, body=None, query_params=None, headers=None):
        uri = self._get_target_uri(uri, query_params)
        data = self._format_body(body)
        return self._request(Methods.PATCH, uri, data, headers)

    def delete(self, uri, body=None, query_params=None, headers=None):
        uri = self._get_target_uri(uri, query_params)
        data = self._format_body(body)
        return self._request(Methods.DELETE, uri, data, headers)


class ClientCSRFApi(ClientApi):
    CSRF_HEADER_FIELD = 'X-CSRFToken'

    def __init__(self, base_url, service_name=None, check_session_id=True):
        super().__init__(base_url, service_name)
        self.check_session_id = check_session_id

    def _update_header_from_cookies(self, resp):
        if resp.cookies:
            if self._cookies and self.check_session_id:
                msg = "You change current sessionId. Better use another client obj for this action"
                assert resp.cookies.get('sessionid') == self._cookies['sessionid'], msg
            self._cookies = resp.cookies.get_dict()
            self.headers.update({self.CSRF_HEADER_FIELD: resp.cookies['csrftoken']})

    def clean_cookies(self):
        self.clean_headers()
        if self._cookies:
            self._cookies = {}

    def clean_headers(self):
        if self.CSRF_HEADER_FIELD in self.headers:
            self.headers.pop(self.CSRF_HEADER_FIELD)


if __name__ == "__main__":
    class TestService(object):

        def __init__(self, client_api):
            self.client = client_api

        def get_account_balance(self, addresses):
            uri = f"/v1/accounts/balances"
            body = {}
            query_params = {"addresses": addresses}
            return self.client.get(uri, body, query_params)

        def get_transaction(self, transactions):
            uri = f"/v1/{transactions}/balances"
            body = {}
            query_params = {}
            return self.client.get(uri, body, query_params)

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


    test = TestService(ClientApi("http://34.254.184.120:8000"))
    test.get_account_balance('0x123weqads123123wqeq')

