
from functools import cached_property

import boto3
try:
    from flask import Response
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from ..base import Boto3Base
from .utils import datetime_to_header


class S3Base(Boto3Base):
    _service = 's3'


class Bucket(S3Base):
    bucket = None

    def __init__(self, bucket, **kwargs):
        if not bucket:
            raise ValueError('bucket must be provided!')

        super().__init__(**kwargs)
        self.bucket = bucket

    def create(self, *, wait=False):
        self._data = self.client.create_bucket(
            Bucket=self.bucket,
        )

        if wait:
            waiter = bucket.client.get_waiter('object_exists')
            waiter.wait(
                Bucket=self.bucket,
            )

    def list(self):
        paginator = self.client.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=self.bucket):
            for item in page.get('Contents', []):
                yield S3Object(self.bucket, item['Key'], autoload=False, **self.init_args)


class Object(S3Base):
    bucket = None
    key = None
    version_id = None
    _obj = None

    def __init__(self, bucket, key, *, version_id=None, autoload=True, **kwargs):
        
        if not bucket or not key:
            raise ValueError('Both bucket and key must be set!')

        super().__init__(**kwargs)
        self.bucket = bucket
        self.key = key
        self.version_id = version_id

        if autoload:
            self.obj = self.get()

    def get(self):
        try:
            kwargs = {
                'Bucket': self.bucket,
                'Key': self.key,
            }
            if self.version_id:
                kwargs.update({
                    'VersionId': self.version_id,
                })
            return self.client.get_object(**kwargs)

        except Exception as exc:  # pylint: disable=broad-except
            print(f'Unable to open: {self.bucket}/{self.key}: {exc}')
            raise exc

    @classmethod
    def create(cls, bucket, key, contents, *, wait=False, **kwargs):
        bucket = S3Bucket(bucket, **kwargs)
        bytes_contents = contents if isinstance(contents, bytes) else contents.encode('utf-8')
        try:
            bucket.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=bytes_contents,
            )

        except Exception as exc:  # pylint: disable=broad-except
            print(f'Unable to save: {bucket}/{key}: {exc}')
            raise exc

        if wait:
            waiter = bucket.client.get_waiter('object_exists')
            waiter.wait(
                Bucket=bucket,
                Key=key,
            )

        return cls(bucket, key, **kwargs)

    def update(self, contents):
        return type(self).create(self.bucket, self.key, contents, **self.init_args)

    def version(self, version):
        if version not in self.versions:
            return None

        return S3Object(
            self.bucket,
            self.key,
            version_id=version,
            **self.init_args,
        )

    @cached_property
    def versions(self):
        versions = {}
        paginator = self.client.get_paginator('list_object_versions')

        version_kwargs = {
            'Bucket': self.bucket,
            'Prefix': self.key,
        }

        for page in paginator.paginate(**version_kwargs):
            for version in page.get('Versions', []):
                versions.update({version['VersionId']: version['LastModified']})

        if 'null' in versions:
            return {}

        return versions

    @property
    def obj(self):
        if not self._obj:
            self._obj = self.get()

        return self._obj

    @obj.setter
    def obj(self, value):
        self._obj = value

    @property
    def content_type(self):
        return self.obj.get('ContentType', None)

    @property
    def cache_control(self):
        return self.obj.get('CacheControl', None)

    @property
    def expires(self):
        return self.obj.get('Expires', None)

    @property
    def last_modified(self):
        return self.obj.get('LastModified', None)

    @property
    def contents(self):
        return self.obj['Body'].read()

    @property
    def flask_response(self):
        if not HAS_FLASK:
            raise AttributeError(
                'Flask is not present in this environment. Cannot produce a Response object.')

        response = Response(response=self.contents)

        if self.content_type:
            response.headers['Content-Type'] = str(self.content_type)
        if self.cache_control:
            response.headers['Cache-Control'] = str(self.cache_control)
        if self.expires:
            response.headers['Expires'] = datetime_to_header(self.expires)
        if self.last_modified:
            response.headers['Last-Modified'] = datetime_to_header(self.last_modified)

        return response
