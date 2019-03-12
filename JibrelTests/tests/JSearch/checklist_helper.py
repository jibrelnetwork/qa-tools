from itertools import product, chain


def names_and_samples(test_data):
    """
    test_data:
      param-1: value
      ...
    """
    names = sorted(list(test_data.keys()))
    samples = [test_data[key] for key in names]
    return dict(argvalues=samples, ids=names)


def names_and_samples_cascade(test_data):
    """
    test_data:
      param-1:
        variant-1: value
      ...
    """
    keys = sorted(list(test_data.keys()))
    mix = [sorted(list(test_data[key].keys())) for key in keys]

    template = ', '.join(['{}={}'] * len(keys))

    names = []
    samples = []
    for item in product(*mix):
        data = list(chain.from_iterable(zip(keys, item)))
        names.append(template.format(*data))

        data = [test_data[key][item[idx]] for idx, key in enumerate(keys)]
        samples.append(data)

    return dict(argvalues=samples, ids=names)
