
from ..base import Boto3Base


class ApiGatewayBase(Boto3Base):
    _service = 'apigateway'

    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.name = name


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
    def id(self):
        return self._data['id']

    @property
    def base_url(self):
        return f'https://{self.id}.execute-api.{self.region}.amazonaws.com'

    def ensure_api_key(self, header, value):
        pass
        


class ApiKey(ApiGatewayBase):

    @classmethod
    def find_by_name(cls, name, **kwargs):
        self = cls(name, **kwargs)
        for key in self.client.paginate('get_api_keys', 'items'):
            if item['name'] == name:
                self._data = item
                return self

        return None

    def create(self, value, *, wait=False):
        kwargs = self.include_tags(
            name=self.name,
            value=value,
        )
        self._data = self.client.create_api_key(**kwargs)


class UsagePlan(ApiGatewayBase):

    pass
