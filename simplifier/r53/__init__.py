
from dataclasses import (
    asdict,
    dataclass,
    is_dataclass,
)
import typing

from ..base import Boto3Base


class Zone(Boto3Base):
    _service = 'route53'
    _zone_id = None
    name = None

    def __init__(self, name, *, zone_id=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.zone_id = zone_id

    @classmethod
    def find_by_domain(cls, domain_name, **kwargs):
        self = cls(domain_name, **kwargs)
        for domain in self.paginate('list_hosted_zones', 'HostedZones'):
            if domain['Name'][:-1].lower() == domain_name.lower():
                self._data = domain
                return self

        return None

    def load(self):
        if self.zone_id:
            self._data = self.client.get_hosted_zone(Id=self.zone_id).get('HostedZone')
        else:
            obj = type(self).find_by_domain(self.name)
            self._data = obj._data

    @property
    def zone_id(self):
        if not self._zone_id:
            self._zone_id = self._data['Id']

        return self._zone_id

    @zone_id.setter
    def zone_id(self, value):
        self._zone_id = value

    def update(self, change_set, *, wait=False):
        changes = asdict(change_set) if is_dataclass(change_set) else change_set

        resp = self.client.change_resource_record_sets(
            HostedZoneId=self.zone_id,
            ChangeBatch=changes,
        )

        if wait:
            self.wait(
                'resource_record_sets_changed',
                Id=resp['ChangeInfo']['Id'],
            )


class Domain(Boto3Base):
    _service = 'route53domains'

    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def register(self, *, num_years=1, admin_contact=None):

        if not admin_contact:
            raise ValueError('admin_contact must be set!')

        self._data = self.client.register_domain(
            DomainName=self.name,
            DurationInYears=num_years,
            AutoRenew=True,
            AdminContact=admin_contact,
            RegistrantContact=admin_contact,
            TechContact=admin_contact,
            BillingContact=admin_contact,
            PrivacyProtectAdminContact=True,
            PrivacyProtectRegistrantContact=True,
            PrivacyProtectTechContact=True,
            PrivacyProtectBillingContact=True,
        )

    @property
    def arn(self):
        raise AttributeError('Domains have no ARN.')

    def load(self):
        self._data = self.client.get_domain_detail(DomainName=self.name)

    @classmethod
    def find_by_domain(cls, domain_name, **kwargs):
        self = cls(domain_name.lower())
        for domain in self.paginate('list_domains', 'Domains'):
            if domain['DomainName'].lower() == self.name:
                self.load()
                return self

        return None


@dataclass(kw_only=True)
class Record:
    Name: str
    Type: str


@dataclass(kw_only=True)
class ResourceRecord(Record):
    TTL: int = 300
    ResourceRecords: typing.Optional[typing.List[typing.Dict[str, str]]]

    @property
    def MultiValueAnswer(self):
        return self.ResourceRecords and len(self.ResourceRecords) > 1


@dataclass(kw_only=True)
class AliasRecord(Record):
    AliasTarget: typing.Dict[str, str]


@dataclass(kw_only=True)
class Change:
    Action: str
    ResourceRecordSet: typing.Union[ResourceRecord, AliasRecord]


@dataclass(kw_only=True)
class ChangeSet:
    Changes: typing.List[Change]
