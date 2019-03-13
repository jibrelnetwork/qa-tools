import logging


log = logging.getLogger(__name__)


class BlockScatter:
    def __init__(self, numbers_list):
        self.numbers_list = numbers_list
        self.min = min(numbers_list)
        self.max = max(numbers_list)
        self.count = len(numbers_list)
        self.scatter = self.max - self.min
        self.k = self.scatter // self.count


def find_overlay_in_etherscan(jsearch_numbers, get_numbers, size):
    """
    Args:
        jsearch_numbers: numbers list of mined blocks or unlces, received from jsearch
        get_numbers: method for finding blocks/uncles in etherscan
        size: etherscan's amount of items for a single page

    Returns:
        Tuple of two elements:
        1) bool result (it is was found overlay in etherscan or not),
        2) list of block numbers found in etherscan
    """

    jsearch = BlockScatter(jsearch_numbers)
    log.info('jsearch min: %s; max: %s' % (jsearch.min, jsearch.max))

    page = 1
    e_scan = BlockScatter(get_numbers(page=page))

    delta = e_scan.min - jsearch.max
    if delta >= 0:
        page_min = 1
        page_max = max(1, delta // size)
    else:  # Something wrong. No reason to find deeper.
        return False, sorted(e_scan.numbers_list)

    overlay = []

    for _ in range(1, page_max + 1):

        if e_scan.min <= jsearch.max <= e_scan.max:
            overlay.extend(e_scan.numbers_list)
            if e_scan.min > jsearch.min:
                overlay.extend(get_numbers(page=page+1))
            return True, sorted(overlay)

        if e_scan.min <= jsearch.min <= e_scan.max:
            overlay.extend(e_scan.numbers_list)
            if page > 1:
                overlay.extend(get_numbers(page=page - 1))
            return True, sorted(overlay)

        message = 'Page: %s. Page min: %s. Page max: %s'
        log.info(message % (page, page_min, page_max))
        log.info('e_scan min: %s; max: %s' % (e_scan.min, e_scan.max))

        if jsearch.max < e_scan.min:
            page_min = page
            estimation = (e_scan.min - jsearch.max) // (size * e_scan.k)
            page = page_min + max(1, estimation)
        if jsearch.min > e_scan.max:
            page_max = page
            estimation = (jsearch.min - e_scan.max) // (size * e_scan.k)
            page = page_max - max(1, estimation)

        e_scan = BlockScatter(get_numbers(page=page))

    return False, sorted(overlay)
