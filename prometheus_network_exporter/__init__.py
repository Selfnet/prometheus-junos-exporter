#!/usr/bin/env python3

__version__ = "0.7.0.11"

from logging import getLogger

from prometheus_client import Histogram, Gauge
from prometheus_client import REGISTRY as DEFAULT_REGISTRY
from tornado.web import Application as _Application

log = getLogger('tornado_prometheus_exporter')


class Application(_Application):
    """ Adds Prometheus integration to Tornado """
    def __init__(self, *args, **kwargs):
        """
        :param prometheus_registry: Prometheus registry that metrics are
            registered to.
        :param int prometheus_port: If not None, start prometheus server with
            given registry on given port.
        :param prometheus_buckets: Gets passed to prometheus_client.Histogram.
        """
        super(Application, self).__init__(*args, **kwargs)

        self.registry = kwargs.pop('registry', DEFAULT_REGISTRY)
        self.max_workers = kwargs.pop('max_workers', 10)
        buckets = kwargs.pop('prometheus_buckets', None)

        histogram_kwargs = {
            'labelnames': ['method', 'handler', 'status'],
            'registry': self.registry,
        }

        # Counter initialization
        self.used_workers = Gauge('network_exporter_used_workers',
                            'The amount of workers being busy scraping Devices.')
        self.total_workers = Gauge('network_exporter_workers',
                            'The total amount of workers')
        self.total_workers.set(self.max_workers)

        self.CONNECTIONS = Gauge('network_exporter_tcp_states',
                            'The count per tcp state and protocol', ['state', 'protocol'])
        if buckets is not None:
            histogram_kwargs['buckets'] = buckets
        self.request_time_histogram = Histogram(
            'tornado_http_request_duration_seconds',
            'Tornado HTTP request duration in seconds',
            **histogram_kwargs)

    def log_request(self, handler):
        """ Adds request metrics to the Prometheus export """
        super(Application, self).log_request(handler)
        self.request_time_histogram \
            .labels(
                method=handler.request.method.lower(),
                handler=type(handler).__name__.lower(),
                status=int(handler.get_status())) \
            .observe(handler.request.request_time())
