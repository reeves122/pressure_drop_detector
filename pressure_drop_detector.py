import urllib.request
import json
import os
import boto3

# Weather location. Ex: 40.7127,-74.0059
LOCATION = os.environ.get('LOCATION')

# Dark Sky API Key
API_KEY = os.environ.get('API_KEY')

# Dark Sky API URL
URL = os.environ.get('URL', f'https://api.darksky.net/forecast/{API_KEY}/{LOCATION}')

# How many hours ahead to calculate a percentage drop
HOURS_AHEAD = int(os.environ.get('HOURS_AHEAD', '24'))

# How many hours ahead to create a warning
WARNING_HOURS_AHEAD = int(os.environ.get('WARNING_HOURS_AHEAD', '6'))

# A warning will be generated if the pressure change percentage is greater than this value
PCT_DROP_THRESHOLD = float(os.environ.get('WARNING_HOURS_AHEAD', '-0.4'))

SNS_TOPIC = os.environ.get('SNS_TOPIC', None)
SNS_CLIENT = boto3.client('sns')

def _calculate_pct_change(original, new):
    """
    Calculate the percentage difference between two numbers

    :param original: the original number
    :param new:      the new number
    :return:         percentage difference between the two numbers
    """
    return round((new - original) / original * 100, 2)


def _convert_hpa_to_inhg(hpa_number):
    """
    Convert hPa to inHg pressure value

    :param hpa_number: the pressure represented as hPa
    :return:           the pressure represented as inHg, rounded to two decimal places
    """
    return round(hpa_number / 33.87, 2)


def lambda_handler(event, context):
    """
    Lamba entry point
    :param event:   Lambda event object
    :param context: Lambda context object
    """
    with urllib.request.urlopen(URL) as response:
        response_dict = json.loads(response.read())

    current_pressure = _convert_hpa_to_inhg(response_dict['currently']['pressure'])
    print(f'Current Pressure: {current_pressure}')

    hourly_pressure = [_convert_hpa_to_inhg(i['pressure']) for i in response_dict['hourly']['data']]

    pct_changes = []
    pct_changes_text = ''
    for i in range(0, HOURS_AHEAD):
        change = _calculate_pct_change(current_pressure, hourly_pressure[i])
        pct_changes.append(change)
        change_text = f'{i} hour pressure: {hourly_pressure[i]}. Change from current: {change}%\n'
        pct_changes_text += change_text

    print(pct_changes_text)

    if pct_changes[WARNING_HOURS_AHEAD] < PCT_DROP_THRESHOLD:
        warning_text = f'WARNING: Large drop in pressure detected in the ' \
                       f'next {WARNING_HOURS_AHEAD} hours! ({pct_changes[WARNING_HOURS_AHEAD]}%)'

        print(warning_text)

        if SNS_TOPIC is not None:
            print(f'Sending event to SNS Topic: {SNS_TOPIC}')
            SNS_CLIENT.publish(
                TopicArn=SNS_TOPIC,
                Message=f'{warning_text}\n\n{pct_changes_text}'
            )


if __name__ == '__main__':
    lambda_handler(None, None)
