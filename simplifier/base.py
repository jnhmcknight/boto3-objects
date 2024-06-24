
from dataclasses import dataclass

import boto3


class Boto3Base:
    _service = None
    _session = None
    _client = None
    _resource = None
    _data = None
    tags = None

    def __init__(self, *, session=None, client=None, tags=None):
        self.session = session
        self.client = client
        self.tags = None
        self._data = {}

    @property
    def init_args(self):
        return {
            'session': self.session,
            'client': self.client,
            'tags': self.tags,
        }

    @property
    def session_args(self):
        return {}

    @property
    def client_args(self):
        return {}

    @property
    def resource_args(self):
        return self.client_args

    @property
    def session(self):
        if not self._session:
            self._session = boto3.session.Session(**self.session_args)

        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    @property
    def client(self):
        if not self._client:
            self._client = self.session.client(self._service, **self.client_args)

        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def resource(self):
        if not self._resource:
            self._resource = self.session.resource(self._service, **self.resource_args)

        return self._resource

    @resource.setter
    def resource(self, value):
        self._resource = value

    def include_tags(self, **kwargs):
        if 'tags' not in kwargs:
            if self.tags:
                kwargs.update({'Tags': self.tags})

        return kwargs

    @property
    def arn(self):
        return self._data['Arn']

    @property
    def in_africa(self):
        return self.region_name.startswith('af-')

    @property
    def in_asia(self):
        return self.region_name.startswith('ap-')

    @property
    def in_canada(self):
        return self.region_name.startswith('ca-')

    @property
    def in_china(self):
        return self.region_name.startswith('cn-')

    @property
    def in_europe(self):
        return self.region_name.startswith('eu-')

    @property
    def in_israel(self):
        return self.region_name.startswith('il-')

    @property
    def in_middle_east(self):
        return self.region_name.startswith('me-')

    @property
    def in_north_america(self):
        return self.in_canada or self._in_usa

    @property
    def in_south_america(self):
        return self.region_name.startswith('sa-')

    @property
    def in_usa(self):
        return self.region_name.startswith('us-')

    @property
    def region_name(self):
        return self.session.region_name

    @property
    def region(self):
        return self.region_name

    @property
    def account_id(self):
        from .sts import STS  # pylint: disable=import-outside-top-level
        return STS(session=self.session).account_id

    def paginate(self, paginator_func, *result_keys, **kwargs):
        paginator = self.client.get_paginator(paginator_func)
        for page in paginator.paginate(**kwargs):
            results = page
            for key in result_keys:
                results = results.get(key, [])
            for item in results:
                yield item

    def wait(self, waiter_func, **kwargs):
        waiter = self.client.get_waiter(waiter_func)
        return waiter.wait(**kwargs)


@dataclass
class Boto3Tag:
    Key: str = None
    Value: str = None
