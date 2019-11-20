from typing import Union


def default(value) -> float:
    return 0 if value is None else float(value)


def is_ok(boolean: Union[bool, str]) -> float:
    if isinstance(boolean, bool):
        if boolean:
            return 1.0
        return 0.0
    elif isinstance(boolean, str):
        if boolean.lower().strip() in ['up', 'ok', 'established']:
            return 1.0
        return 0.0
    elif boolean is None:
        return 0.0
    else:
        raise Exception("Unknown Type: {}".format(boolean))


def boolify(string: str) -> bool:
    return 'true' in string.lower()


def none_to_zero(string) -> float:
    return default(string)


def none_to_minus_inf(string) -> float:
    return - float('inf') if string is None else string


def none_to_plus_inf(string) -> float:
    return float('inf') if string is None else string


def floatify(string: Union[str, float]) -> float:
    if isinstance(string, str):
        if "- Inf" in string:
            return - float('inf')
        elif "Inf" in string:
            return float('inf')
    return float(string) if string is not None else none_to_zero(string)

# The complex Functions


def fan_power_temp_status(metric, registry, labels, data, create_metric=None):
    for sensorname, information in data.items():
        labels['sensorname'] = sensorname
        create_metric(metric, registry, 'status', labels,
                      information, function='is_ok')


def temp_celsius(metric, data, create_metric=None):
    for sensorname, information in data.items():
        labels['sensorname'] = sensorname
        create_metric(metric, registry, 'temperature',
                      labels, information)


def reboot(metric, data):
    reason_string = data.get('last_reboot_reason', '')
    reason = 1
    for a in ["failure", "error", "failed"]:
        if a in reason_string.lower():
            reason = 0
    labels['reboot_reason'] = reason_string
    registry.add_metric(metric, reason, labels=labels)


def cpu_usage(metric, data):
    for slot, perf in data.items():
        label = "cpu_{}".format(str(slot))
        labels['cpu'] = label
        cpu_usage = 100 - int(perf['cpu-idle'])
        registry.add_metric(metric, cpu_usage, labels=labels)


def cpu_idle(metric, data):
    for slot, perf in data.items():
        label = "cpu_{}".format(str(slot))
        labels['cpu'] = label
        cpu_idle = int(perf['cpu-idle'])
        registry.add_metric(metric, cpu_idle, labels=labels)


def ram_usage(metric, data):
    for slot, perf in data.items():
        label = "ram_{}".format(str(slot))
        labels['ram'] = label
        memory_complete = perf['memory-dram-size'].lower().replace("mb",
                                                                   "").strip()
        memory_complete = int(memory_complete)
        memory_usage = int(perf['memory-buffer-utilization'])
        memory_bytes_usage = (memory_complete * memory_usage / 100) * 1049000
        registry.add_metric(metric, memory_bytes_usage, labels=labels)


def ram(metric, data):
    for slot, perf in data.items():
        label = "ram_{}".format(str(slot))
        labels['ram'] = label
        memory_complete = perf['memory-dram-size'].lower().replace("mb",
                                                                   "").strip()
        memory_complete = int(memory_complete)
        memory_bytes = memory_complete * 1049000
        registry.add_metric(metric, memory_bytes, labels=labels)
