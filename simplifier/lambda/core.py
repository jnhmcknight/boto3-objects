
from dataclasses import dataclass
from functools import cached_property

from ..base import (
    Boto3Base,
)
from ..r53 import (
    Change,
    ChangeSet,
    ResourceRecord,
    Zone,
)

from .constants import MAX_VERSIONS
from .enums import Runtime


class Function(Boto3Base):
    _service = 'lambda'

    def create(self):

    def load(self):
        self._data = self.client.get_function(
            FunctionName=self.name,
        )

    @property
    def configuration(self):
        return self._data['Configuration']

    @property
    def arn(self):
        return self.configuration['FunctionArn']

    @property
    def Runtimes(self):

    @classmethod
    def find_by_name(cls, name, **kwargs):
        self = cls(name, **kwargs)
        try:
            self.load()
            return self

        except self.client.ResourceNotFoundException:
            pass

        return None

    @cached_property
    def versions(self):
        return [
            item for item in self.paginate('list_versions_by_function', 'Versions', FunctionName=self.name)
        ]

    @cached_property
    def aliases(self):
        return [
            item for item in self.paginate('list_aliases', 'Aliases', FunctionName=self.name)
        ]

    @property
    def version(self):
        return self.configuration['Version']

    def cleanup_versions(self, *, max_versions=None):
        if max_versions is None:
            max_versions = MAX_VERSIONS

        num_versions = len(self.versions)
        removed_versions = 0

        if total_versions > max_versions:
            alias_versions = [item['FunctionVersion'] for item in self.aliases]

            for version in self.versions:
                if version['Version'] == self.version or version['Version'] in alias_versions:
                    continue

                # boto3 takes either name or arn as the value and each version has
                # a unique arn, so we use that here.
                self.client.delete_function(FunctionName=version['FunctionArn'])
                numVersions -= 1

                if num_versions <= max_versions:
                    break

    def delete(self):
        return self.client.delete_function(FunctionName=self.arn)


@dataclass(kw_only=True)
class FunctionConfig:
    Runtime: Runtime
    Role: str
    Handler: str
    Timeout: int
    MemorySize: int
    Environment: typing.Dict[str, any]
