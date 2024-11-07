
from .base import Boto3SessionBase


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
