
from datetime import datetime

from ..base import Boto3Base
from ..r53 import (
    AliasRecord,
    Change,
    ChangeSet,
)


class Distribution(Boto3Base):
    _service = 'cloudfront'
    config = None

    def __init__(self, config, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    @property
    def _cloudfront_zone_id(self):
        return 'Z3RFFRIM2A3IF5' if self.in_china else 'Z2FDTNDATAQYW2'

    def create(self, *, wait=False):
        kwargs = self.include_tags(**self.config)
        kwargs.update({'CallerReference': str(datetime.utcnow().timestamp())})

        if self.tags:
            self._data = self.client.create_distribution_with_tags(
                DistributionConfigWithTags=kwargs,
            ).get('Distribution')

        else:
            self._data = self.client.create_distribution(
                DistributionConfig=kwargs,
            ).get('Distribution')

        if wait:
            self.wait(
                'distribution_deployed',
                Id=self.id,
            )

    @classmethod
    def find_by_domain_name(cls, domain_name, **kwargs):
        self = cls({})
        for distro in self.paginate('list_distributions', 'DistributionList', 'Items'):
            if domain_name in distro.get('Aliases', {}).get('Items', []):
                self._data = distro
                return self

        return None

    @property
    def id(self):
        return self._data['Id']

    @property
    def domain_name(self):
        return self._data['DomainName']

    @property
    def custom_domain_name(self):
        aliases = self._data.get('Aliases', self.config.get('Aliases'))
        return aliases['Items'][0]

    def dns_aliases(self):
        alias_target = {
            'HostedZoneId': self._cloudfront_zone_id,
            'DNSName': self.domain_name,
            'EvaluateTargetHealth': False,
        }

        ipv4_alias = AliasRecord(
            Name=self.custom_domain_name,
            Type='A',
            AliasTarget=alias_target,
        )
        ipv6_alias = AliasRecord(
            Name=self.custom_domain_name,
            Type='AAAA',
            AliasTarget=alias_target,
        )

        return ChangeSet(
            Changes=[
                Change(
                    Action='UPSERT',
                    ResourceRecordSet=ipv4_alias,
                ),
                Change(
                    Action='UPSERT',
                    ResourceRecordSet=ipv6_alias,
                ),
            ]
        )


class Function(Boto3Base):
    _service = 'cloudfront'
    name = None
    code = None
    _comment = None
    _runtime = None
    etag = None

    def __init__(self, name, code, *, comment=None, runtime=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.code = code
        self.comment = comment
        self.runtime = runtime

    def create(self):
        kwargs = {
            'Name': self.name,
            'FunctionCode': self.code if isinstance(self.code, bytes) else self.code.encode('utf-8'),
            'FunctionConfig': {
                'Comment': self.comment,
                'Runtime': self.runtime,
            },
        }

        resp = self.client.create_function(**kwargs).get('FunctionSummary')
        self._data = resp.get('FunctionSummary')
        self.etag = resp.get('ETag')

        self.client.publish_function(
            Name=self.name,
            IfMatch=self.etag,
        )

    def load(self):
        self._data = self.client.describe_function(Name=self.name).get('FunctionSummary')
        resp = self.client.get_function(Name=self.name)
        self.code = resp['FunctionCode'].read()
        self.etag = resp['ETag']

    @property
    def status(self):
        if not self._data.get('FunctionMetadata'):
            self.load()

        return self._data['FunctionMetadata']['Stage']

    @property
    def arn(self):
        if not self._data.get('FunctionMetadata'):
            self.load()

        return self._data['FunctionMetadata']['FunctionARN']

    @property
    def comment(self):
        if self._comment is None:
            return ''

        return self._comment

    @comment.setter
    def comment(self, value):
        self._comment = value

    @property
    def runtime(self):
        if self._runtime is None:
            self._runtime = 'cloudfront-js-2.0'

        return self._runtime

    @runtime.setter
    def runtime(self, value):
        self._runtime = value

    @classmethod
    def find_by_name(cls, name):
        self = cls(name, None)
        try:
            resp = self.client.get_function(Name=self.name)
            self.code = resp['FunctionCode'].read()
            self.etag = resp['ETag']
            return self
        except self.client.exceptions.NoSuchFunctionExists:
            return None
