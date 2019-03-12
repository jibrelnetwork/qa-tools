from qa_tool.utils.utils import getter


def check_status(status_data, expected_error):
    """
    :param status_data: {'success': boolean, 'errors': []}
    """
    if expected_error:
        validate(status_data, expected_error)


def get_interest_data(data, expected_error=None):
    if isinstance(data, dict) and 'status' in data and 'data' in data:
        check_status(data['status'], expected_error)
        data = data['data']
    return data


def sorted_actual_and_expected_data(data, expected_data):
    if data:
        item = data[0]
        if not isinstance(item, dict):
            return sorted(data), sorted(expected_data)
        elif 'id' in data[0] and 'id' in expected_data[0]:
            _sort = lambda _data: sorted(_data, key=lambda i: i['id'])
            return _sort(data), _sort(expected_data)
    return data, expected_data


def validate(data, expected_data, ignore_ordering=True, strict_mode=False, expected_error=None):
    _fn_validate = lambda _data, _expected_data: validate(_data, _expected_data, ignore_ordering, strict_mode, None)
    data = get_interest_data(data, expected_error)

    if isinstance(data, dict):
        diff_keys = set(expected_data.keys()) - set(data.keys())
        assert not diff_keys, "Expected data has more key, then actual data: %s" % str(diff_keys)
        for field_name, value in expected_data.items():
            try:
                _fn_validate(data[field_name], value)
            except AssertionError as err_msg:
                msg = '\n'.join([
                    str(err_msg),
                    "Problem with key %s:" % field_name,
                    "    Actual result: %s" % data.get(field_name),
                    "    Expected result: %s" % value
                ])
                raise AssertionError(msg)

    elif isinstance(data, (list, tuple)):
        assert isinstance(expected_data, (list, tuple))
        assert len(data) == len(expected_data), "Different length between expected_data and actual data"
        data, expected_data = sorted_actual_and_expected_data(data, expected_data)
        for i in range(len(expected_data)):
            _fn_validate(data[i], expected_data[i])

    elif data is None or isinstance(data, bool):
        assert any([expected_data is i for i in  [None, True, False]])

    else:
        assert type(data) == type(expected_data)
        assert data == expected_data


if __name__ == "__main__":
    # data = {
    #     'test1': 1,
    #     'test_not_check': 123,
    #     'array1': [2,1,3]
    # }
    #
    # expected_data = {
    #     'test1': 1,
    #     'array1': [1,2,3,4],
    # }
    # validate(data, expected_data)

    validate(True, 1)
