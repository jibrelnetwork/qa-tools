

def non_strict_check_number(data, expected_data, delta):
    msg = f"{expected_data - delta} <= {data}(Actual result) <= {expected_data + delta}"
    assert expected_data - delta <= data <= expected_data + delta, msg


common_strict_mapping = {
    int: non_strict_check_number,
    float: non_strict_check_number
}


def check_status(status_data, expected_error):
    """
    :param status_data: {'success': boolean, 'errors': []}
    """
    if expected_error:
        validate(status_data, expected_error)


def get_interest_data(data, expected_error=None):
    if not isinstance(data, dict):
        return data
    if 'status' in data:
        check_status(data['status'], expected_error)
    if 'data' in data:
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


def validate(data, expected_data, ignore_ordering=True, strict_mode=True, expected_error=None, strict_delta_by_type=None):
    """
    :param strict_mode:
    :param strict_mapping: like {int: 1, float: 0.002}
    """
    _fn_validate = lambda _data, _expected_data: validate(_data, _expected_data, ignore_ordering, strict_mode, None, strict_delta_by_type)
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
        expected_type = type(expected_data)
        if strict_mode or expected_type not in common_strict_mapping:
            assert type(data) == expected_type
            assert data == expected_data
        else:
            strict_delta_by_type = strict_delta_by_type or {}
            data = expected_type(data)
            delta = strict_delta_by_type.get(expected_type, 0.5)
            common_strict_mapping[expected_type](data, expected_data, delta)


class TestValidator:

    def test_sample(self):
        data = {
            'test1': 1,
            'test_not_check': 123,
            "test_qwe": 10
        }

        expected_data = {
            'test1': 1,
            'test_not_check': 123,
        }
        validate(data, expected_data)

    def t1est_strict_mode_for_float(self):
        data = {'var': 1.3}
        expected_data = {'var': 1.5}
        validate(data, expected_data, strict_mode=False, strict_delta_by_type={float: 0.2})

    def test_strict_mode_for_float_negative(self):
        data = {'var': 1.3}
        expected_data = {'var': 1.5}
        validate(data, expected_data, strict_mode=False, strict_delta_by_type={float: 0.1})


if __name__ == "__main__":
    from qa_tool import run_test
    run_test(__file__)

    # validate(True, 1)
