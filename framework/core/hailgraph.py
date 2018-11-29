
import numpy
import pandas
import sys


def read_file(filename):
    data = pandas.read_csv(filename)
    data.index = pandas.to_datetime(data.timeStamp, unit='ms')
    return data


def resample(filename, offset_seconds=0, constant_seconds=0):
    data = read_file(filename)
    data_start = int(data.iloc[0]['timeStamp'])
    data_end = int(data.iloc[-1]['timeStamp'])
    constant_start = data_start + (offset_seconds * 1000)
    if constant_seconds == 0:
        constant_seconds = int((data_end - constant_start) / 1000)
    constant_end = constant_start + (constant_seconds * 1000)
    constant_phase = data[(data['timeStamp'] >= constant_start) & (data['timeStamp'] <= constant_end)]
    overall_data = constant_phase.elapsed.resample('24h').apply(
        {
            'tot': numpy.size
        }
    )
    resampled_data = data.elapsed.resample('1s')
    agg_data = pandas.DataFrame(resampled_data.agg(['mean', 'median', 'std', 'min', 'max', 'size']))
    agg_data['rps'] = resampled_data.agg({'rps': numpy.size}).fillna(0).values
    agg_data['clients'] = data.allThreads.resample('1s').agg({'clients': numpy.min}).fillna(0).values
    agg_data['4xx'] = data.responseCode[(data.responseCode >= 400) & (data.responseCode < 500)].resample('1s').count()
    agg_data['4xx'] = agg_data['4xx'].fillna(0).astype(int)
    agg_data['5xx'] = data.responseCode[(data.responseCode >= 500)].resample('1s').count()
    agg_data['5xx'] = agg_data['5xx'].fillna(0).astype(int)
    agg_data.to_csv(filename + '.sec.csv')
    data_frame_to_json(agg_data, ['date', 'rps'], filename + '.sec.json')


def data_frame_to_json(data, series, filename):
    pass


def make_html(filename, template):
    pass



def usage():
    print("usage: hailgraph.py verb -l|--log_filename log_filename [options]")
    print("       verbs:")
    print("                         resample                    Reads the base csv file and resample into seconds")
    print("                                                     based data and stores that as <filename>.sec.csv")
    print("                         html                        Create SPA html page.")
    print("                         generate                    Generate graphs based on the resample file.")
    print("                         full                        Convenient verb to perform both resample and generate.")
    print("       options:")
    print("                         -c|--constant_seconds       The number of seconds that is considered to be part")
    print("                                                     of the constant phase.")
    print("                         -p|--profile                profile to be used.")
    print("                         --params                    additional params to be overridden.")
    print("                         -o|--offset_seconds         The number of seconds in the beginning that is not")
    print("                                                     part of the constant phase.")
    print("")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        usage()
        exit(1)
    verb = sys.argv[1]
    script = ''
    profile = ''
    params = ''
    _offset_seconds = 0
    log_file = ''
    _html_template = ''
    while len(sys.argv) > 2:
        switch = sys.argv.pop(2)
        if switch in '--profile':
            profile = sys.argv.pop(2)
        if switch in '--params':
            params = sys.argv.pop(2)
        if switch in '--offset_seconds':
            _offset_seconds = int(sys.argv.pop(2))
        if switch in '--log_filename':
            log_file = sys.argv.pop(2)
        if switch in '--template':
            _html_template = sys.argv.pop(2)
    if log_file == '':
        usage()
        exit(1)
    if verb == 'resample':
        resample(log_file, _offset_seconds)
    if verb == 'html':
        make_html(log_file, _html_template)
    if verb == 'get_running_profile':
        pass

