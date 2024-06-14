
from ..base import Boto3Base


class STS(Boto3Base):

    @property
    def identity(self):
        return self.client.get_caller_identity()

    @property
    def account_id(self):
        return self.identity['Account']
