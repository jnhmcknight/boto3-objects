
from dataclasses import (
    asdict,
    dataclass,
)
import json
import typing

from ..base import Boto3Base


class ApiGatewayBase(Boto3Base):
    _service = 'apigateway'

    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def include_tags(self, **kwargs):
        return super().include_tags(tag_key='tags', **kwargs)

    @property
    def id(self):
        return self._data['id']


class Gateway(ApiGatewayBase):

    @classmethod
    def find_by_name(cls, name, **kwargs):
        self = cls(name)
        for item in self.paginate('get_rest_apis', 'items'):
            if item['name'] == self.name:
                self._data = item
                return self

        return None

    @property
    def base_url(self):
        return f'https://{self.id}.execute-api.{self.region}.amazonaws.com'

    def ensure_api_key(self, name, key):
        api_key = ApiKey.find_by_name(name)
        if not api_key:
            api_key = ApiKey(name, value=key, **self.init_args)
            api_key.create()

        usage_plan = UsagePlan.find_by_name(name)
        if not usage_plan:
            usage_plan = UsagePlan(name)
            usage_plan.create(api_gateway=self)

        usage_plan.ensure_stage(self)
        usage_plan.add_key(api_key)

        for resource in self.paginate('get_resources', 'items', restApiId=self.id):
            for method, data in resource.get('resourceMethods', {}).items():
                if data.get('apiKeyRequired'):
                    continue

                self.client.update_method(
                   restApiId=self.id,
                   resourceId=resource['id'],
                   httpMethod=method,
                   patchOperations=[{
                       'op': 'replace',
                       'path': '/apiKeyRequired',
                       'value': 'true',
                   }],
                )

    @property
    def stages(self):
        return [GatewayStage(deploymentId=item['deploymentId'], stageName=item['stageName']) for item in self.client.get_stages(restApiId=self.id).get('item')]


@dataclass(kw_only=True)
class GatewayStage:
    deploymentId: str
    stageName: str

    @property
    def id(self):
        return self.deploymentId

    @property
    def name(self):
        return self.stageName


class ApiKey(ApiGatewayBase):
    value = None

    def __init__(self, name, *, value=None, **kwargs):
        super().__init__(name, **kwargs)
        self.value = value

    @classmethod
    def find_by_name(cls, name, **kwargs):
        self = cls(name, **kwargs)
        for item in self.paginate('get_api_keys', 'items'):
            if item['name'] == name:
                self._data = item
                return self

        return None

    def create(self, *, value=None, wait=False):
        if value is None:
            if self.value is None:
                raise ValueError(
                    'Either provide a value when creating the ApiKey object, or when calling create()'
                )

            value = self.value

        kwargs = self.include_tags(
            name=self.name,
            value=value,
        )
        self._data = self.client.create_api_key(**kwargs)


class UsagePlan(ApiGatewayBase):

    @classmethod
    def find_by_name(cls, name, **kwargs):
        self = cls(name, **kwargs)
        for item in self.paginate('get_usage_plans', 'items'):
            if item['name'] == self.name:
                self._data = item
                return self

        return None

    def create(self, *, api_gateway=None):
        kwargs = self.include_tags(
            name=self.name,
        )

        if api_gateway is not None:
            new_stages = []
            for stage in api_gateway.stages:
                usage_plan_stage = UsagePlanStage(
                    apiId=api_gateway.id,
                    stage=stage.name,
                )
                new_stages.append(asdict(usage_plan_stage))

            if new_stages:
                kwargs.update({
                    'apiStages': new_stages,
                })

        self._data = self.client.create_usage_plan(**kwargs)

    @property
    def stages(self):
        return [UsagePlanStage(apiId=item['apiId'], stage=item['stage']) for item in self._data.get('apiStages')]

    def ensure_stage(self, api_gateway):
        stages = self.stages
        for stage in api_gateway.stages:
            usage_plan_stage = UsagePlanStage(
                apiId=api_gateway.id,
                stage=stage.name,
            )
            if usage_plan_stage not in stages:
                self.client.update_usage_plan(
                    usagePlanId=self.id,
                    patchOperations=[{
                        'op': 'add',
                        'path': '/apiStages',
                        'value': f'{usage_plan_stage.apiId}:{usage_plan_stage.stage}',
                    }],
                )

    def add_key(self, api_key):
        try:
            self.client.get_usage_plan_key(
                usagePlanId=self.id,
                keyId=api_key.id,
            )
        except self.client.exceptions.NotFoundException:
            self.client.create_usage_plan_key(
                usagePlanId=self.id,
                keyId=api_key.id,
                keyType='API_KEY',
            )


@dataclass(kw_only=True)
class UsagePlanStage:
    apiId: str
    stage: str

    def __eq__(self, other):
        return self.apiId == other.apiId and self.stage == other.stage
