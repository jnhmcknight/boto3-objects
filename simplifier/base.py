
from dataclasses import dataclass
import typing

import boto3
import botocore


@dataclass
class Boto3Tag:
    Key: str = None
    Value: str = None


class Boto3SessionBase:
    _service: str = None
    _session: boto3.session.Session = None
    _session_args: typing.Dict[str, any] = None

    def __init__(
        self, *,
        session: boto3.session.Session = None,
        **session_args,
    ):

        self.session = session
        self.session_args = session_args

    @property
    def service(self):
        return self._service

    @property
    def session_args(self):
        return self._session_args or {}

    @session_args.setter
    def session_args(self, value):
        if value is None:
            self._session_args = {}

        elif isinstance(value, dict):
            self._session_args = value

        else:
            raise ValueError('Invalid value provided for session args')

    @property
    def session(self):
        if not self._session:
            self._session = boto3.session.Session(**self.session_args)

        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    @property
    def account_id(self):
        from .sts import STS  # pylint: disable=import-outside-top-level
        return STS(session=self.session).account_id

    @property
    def region_name(self):
        return self.session.region_name

    @property
    def region(self):
        return self.region_name

    @property
    def in_australia(self):
        return self.region_name in [
            'ap-southeast-2',  # Melbourne
            'ap-southeast-4',  # Syndey
        ]

    @property
    def in_canada(self):
        return self.region_name.startswith('ca-')

    @property
    def in_china(self):
        return self.region_name.startswith('cn-')

    @property
    def in_israel(self):
        return self.region_name.startswith('il-')

    @property
    def in_south_africa(self):
        return self.region_name in [
            'af-south-1',  # Cape Town
        ]

    @property
    def in_usa(self):
        return self.region_name.startswith('us-')

    @property
    def in_africa(self):
        return self.region_name.startswith('af-')

    @property
    def in_asia(self):
        return self.region_name.startswith('ap-')

    @property
    def in_europe(self):
        return self.region_name.startswith('eu-')

    @property
    def in_middle_east(self):
        return self.region_name.startswith('me-')

    @property
    def in_north_america(self):
        return self.in_canada or self._in_usa

    @property
    def in_south_america(self):
        return self.region_name.startswith('sa-')


class Boto3Base(Boto3SessionBase):
    _client: botocore.client.BaseClient = None
    _client_args: botocore.client.Config = None
    _resource: boto3.resources.model.ResourceModel = None
    _data: typing.Dict[str, any] = None
    tags: typing.List[Boto3Tag] = None

    def __init__(
        self, *,
        tags: typing.List[Boto3Tag] = None,
        client: botocore.client.BaseClient = None,
        client_args: botocore.client.Config = None,
        session: boto3.session.Session = None,
        **session_args,
    ):
        super().__init__(session=session, **session_args)

        self.client = client
        self.client_args = client_args
        self.tags = None
        self._data = {}

    @property
    def init_args(self):
        return {
            'session': self.session,
            'client_args': self.client_args,
            'tags': self.tags,
        }

    @property
    def client_args(self):
        return self._client_args or {}

    @client_args.setter
    def client_args(self, value: typing.Union[botocore.client.Config, None]):
        if value is None:
            self._client_args = {}
        else:
            self._client_args = value

    @property
    def client(self):
        if not self._client:
            self._client = self.session.client(self.service, **self.client_args)

        return self._client

    @client.setter
    def client(self, value: botocore.client.BaseClient):
        self._client = value

    @property
    def resource(self):
        if not self._resource:
            self._resource = self.session.resource(self.service, **self.client_args)

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
