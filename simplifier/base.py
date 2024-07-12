
from dataclasses import dataclass

import boto3


class Boto3SessionBase:
    _service = None
    _session = None

    def __init__(self, *, session=None):
        self.session = session

    @property
    def service(self):
        return self._service

    @property
    def session_args(self):
        return {}

    @property
    def session(self):
        if not self._session:
            self._session = boto3.session.Session(**self.session_args)

        return self._session

    @session.setter
    def session(self, value):
        self._session = value


class Boto3Enum(Boto3SessionBase):
    _instances = {}

    def __new__(cls, service, *args, **kwargs):
        if service not in cls._instance:
            cls._instances[service] = super().__new__(cls, *args, **kwargs)
            cls._instances[service]._service = service

        return cls._instances[service]

    def service_model(self):
        return self.session.get_service_model(self.service)

    def operation_model(self, name):
        return self.service_model.operation_model(name)

    def operation_enum(self, operation_model, member):
        return self.operation_model(operation_model).input_shape.members(member).enum


class Boto3Base(Boto3SessionBase):
    _client = None
    _resource = None
    _data = None
    tags = None

    def __init__(self, *, client=None, tags=None, **kwargs):
        super().__init__(**kwargs)

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
    def client_args(self):
        return {}

    @property
    def resource_args(self):
        return self.client_args

    @property
    def client(self):
        if not self._client:
            self._client = self.session.client(self.service, **self.client_args)

        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def resource(self):
        if not self._resource:
            self._resource = self.session.resource(self.service, **self.resource_args)

        return self._resource

    @resource.setter
    def resource(self, value):
        self._resource = value

    def include_tags(self, *, tag_key='Tags', **kwargs):
        if 'tags' not in kwargs:
            if self.tags:
                kwargs.update({tag_key: self.tags})

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
