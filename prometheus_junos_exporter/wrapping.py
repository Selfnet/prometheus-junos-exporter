
#!/usr/bin/env python3
import sys
import os
import time
import datetime
from getpass import getpass, getuser
import yaml
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
# If u want to have more metrics. You must edit the config/metrics_definitions.yml
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config', 'metrics_definition.yml'), 'r') as metrics_definitions:
    DEFINITIONS = yaml.load(metrics_definitions).get('DEFINITIONS', {})

# Get the Metrics DEFINITIONS
METRICS_BASE = DEFINITIONS.get('METRICS_BASE', {})
NETWORK_REGEXES = DEFINITIONS.get('NETWORK_REGEXES', [])
NETWORK_METRICS = DEFINITIONS.get('NETWORK_METRICS', {})
ENVIRONMENT_METRICS = DEFINITIONS.get('ENVIRONMENT_METRICS', {})
NETWORK_LABEL_WRAPPER = DEFINITIONS.get('NETWORK_LABEL_WRAPPER', [])
ENVIRONMENT_LABEL_WRAPPER = DEFINITIONS.get('ENVIRONMENT_LABEL_WRAPPER', [])
BGP_METRICS = DEFINITIONS.get('BGP_METRICS', {})
BGP_LABEL_WRAPPER = DEFINITIONS.get('BGP_LABEL_WRAPPER', [])

global FUNCTIONS


def init():
    global FUNCTIONS, METRICS
    FUNCTIONS = {
        'is_ok': is_ok,
        'flap': flap,
        'temp': temp,
        'intify': intify,
        'floatify': floatify,
        'fan_power_temp_status': fan_power_temp_status,
        'temp_celsius': temp_celsius,
        'reboot': reboot,
        'cpu_idle': cpu_idle,
        'cpu_usage': cpu_usage,
        'ram': ram,
        'ram_usage': ram_usage
    }

    METRICS = {
        'Counter': 'counter',
        'Gauge': 'gauge'
    }


def is_ok(boolean):
    if isinstance(boolean, bool):
        if boolean:
            return 1
        return 0
    elif isinstance(boolean, str):
        if boolean.lower() in ['up', 'ok', 'established']:
            return 1
        return 0
    else:
        raise Exception("Unknown Type")


def flap(string):
    if 'never' in string.lower():
        return 0
    string = string.split(" (")[0]
    val = time.mktime(datetime.datetime.strptime(
        string, "%Y-%m-%d %H:%M:%S %Z").timetuple())
    return val


def temp(string):
    string = int(string.split(' ')[0])
    return string


def intify(string):
    return int(string)


def floatify(string):
    return float(string)


def boolify(string):
    return 'true' in string.lower()


def fan_power_temp_status(metrik, registry, labels, data, create_metrik=None):
    for sensorname, information in data.items():
        labels['sensorname'] = sensorname
        create_metrik(metrik, registry, 'status', labels,
                      information, function='is_ok')


def temp_celsius(metrik, registry, labels, data, create_metrik=None):
    for sensorname, information in data.items():
        labels['sensorname'] = sensorname
        create_metrik(metrik, registry, 'temperature',
                      labels, information, function='intify')


def reboot(metrik, registry, labels, data, create_metrik=None):
    reason_string = data['last_reboot_reason']
    reason = 1
    for a in ["failure", "error", "failed"]:
        if a in reason_string.lower():
            reason = 0
    labels['reboot_reason'] = reason_string
    registry.add_metric(metrik, reason, labels=labels)


def cpu_usage(metrik, registry, labels, data, create_metrik=None):
    for slot, perf in data.items():
        label = "cpu_{}".format(str(slot))
        labels['cpu'] = label
        cpu_usage = 100 - int(perf['cpu-idle'])
        registry.add_metric(metrik, cpu_usage, labels=labels)


def cpu_idle(metrik, registry, labels, data, create_metrik=None):
    for slot, perf in data.items():
        label = "cpu_{}".format(str(slot))
        labels['cpu'] = label
        cpu_idle = int(perf['cpu-idle'])
        registry.add_metric(metrik, cpu_idle, labels=labels)


def ram_usage(metrik, registry, labels, data, create_metrik=None):
    for slot, perf in data.items():
        label = "ram_{}".format(str(slot))
        labels['ram'] = label
        memory_complete = perf['memory-dram-size'].lower().replace("mb",
                                                                   "").strip()
        memory_complete = int(memory_complete)
        memory_usage = int(perf['memory-buffer-utilization'])
        memory_bytes_usage = (memory_complete * memory_usage / 100) * 1049000
        registry.add_metric(metrik, memory_bytes_usage, labels=labels)


def ram(metrik, registry, labels, data, create_metrik=None):
    for slot, perf in data.items():
        label = "ram_{}".format(str(slot))
        labels['ram'] = label
        memory_complete = perf['memory-dram-size'].lower().replace("mb",
                                                                   "").strip()
        memory_complete = int(memory_complete)
        memory_bytes = memory_complete * 1049000
        registry.add_metric(metrik, memory_bytes, labels=labels)


def create_metrik_params(metrik_def, call='interfaces'):
    metrik_name = metrik_def['metrik']
    key = metrik_def['key']
    description = metrik_def.get('description', '')
    type_of = metrik_def.get('type', None)
    function = metrik_def.get('function', None)
    specific = metrik_def.get('specific', False)
    if type_of:
        metrik_name = '{}_{}'.format(metrik_name, type_of)
    return metrik_name, description, key, function, specific


def create_metrik(metrik_name, registry, key, labels, metriken, function=None):
    if metriken.get(key) is not None:
        try:
            if function:
                registry.add_metric(metrik_name, FUNCTIONS[function](
                    metriken.get(key)), labels=labels)
            else:
                registry.add_metric(
                    metrik_name, metriken.get(key), labels=labels)
        except (ValueError, KeyError) as e:
            print("Error :: {}".format(e))