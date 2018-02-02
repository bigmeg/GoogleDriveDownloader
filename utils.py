import re, sys, math


def sizeof_human(num):
    '''
    Human-readable formatting for filesizes. Taken from `here <http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size>`_.

    >>> sizeof_human(175799789)
    '167.7 MB'

    :param num: Size in bytes.
    :type num: int

    :rtype: string
    '''
    unit_list = list(zip(['B', 'kB', 'MB', 'GB', 'TB', 'PB'], [0, 0, 1, 2, 2, 2]))
    num = int(num)
    if num > 1:
        exponent = min(int(math.log(num, 1024)), len(unit_list) - 1)
        quotient = float(num) / 1024 ** exponent
        unit, num_decimals = unit_list[exponent]

        if sys.version_info >= (2, 7):  # python2.7 supports comma seperators
            format_string = '{:,.%sf} {}' % (num_decimals)
            return format_string.format(quotient, unit)
        else:  # with python2.6, we have to do some ugly hacks
            if quotient != int(quotient):  # real float
                x, y = str(quotient).split('.')
                x = re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1,", "%d" % int(x))
                y = y[:num_decimals]
                quotient = "%s.%s" % (x, y) if y else x
                return "%s %s" % (quotient, unit)
            else:
                quotient = re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1,", "%d" % quotient)
                return "%s %s" % (quotient, unit)

    if num == 0:
        return '0 bytes'
    if num == 1:
        return '1 byte'


def time_human(duration, fmt_short=False):
    '''
    Human-readable formatting for timing. Based on code from `here <http://stackoverflow.com/questions/6574329/how-can-i-produce-a-human-readable-difference-when-subtracting-two-unix-timestam>`_.

    >>> time_human(175799789)
    '6 years, 2 weeks, 4 days, 17 hours, 16 minutes, 29 seconds'
    >>> time_human(589, fmt_short=True)
    '9m49s'

    :param duration: Duration in seconds.
    :type duration: int
    :param fmt_short: Format as a short string (`47s` instead of `47 seconds`)
    :type fmt_short: bool
    :rtype: string
    '''
    duration = int(duration)
    if duration == 0:
        return "0s" if fmt_short else "0 seconds"

    INTERVALS = [1, 60, 3600, 86400, 604800, 2419200, 29030400]
    if fmt_short:
        NAMES = ['s' * 2, 'm' * 2, 'h' * 2, 'd' * 2, 'w' * 2, 'y' * 2]
    else:
        NAMES = [('second', 'seconds'),
                 ('minute', 'minutes'),
                 ('hour', 'hours'),
                 ('day', 'days'),
                 ('week', 'weeks'),
                 ('month', 'months'),
                 ('year', 'years')]

    result = []

    for i in range(len(NAMES) - 1, -1, -1):
        a = duration // INTERVALS[i]
        if a > 0:
            result.append((a, NAMES[i][1 % a]))
            duration -= a * INTERVALS[i]

    if fmt_short:
        return "".join(["%s%s" % x for x in result])
    return ", ".join(["%s %s" % x for x in result])
