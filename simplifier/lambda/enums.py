
from ..base import Boto3Enum


enums = Boto3Enum('lambda')

Runtime = enums.operation_enum('CreateFunction', 'Runtime')
