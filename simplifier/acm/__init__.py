

from ..base import Boto3Base
from ..r53 import (
    Change,
    ChangeSet,
    ResourceRecord,
    Zone,
)


class Certificate(Boto3Base):
    _service = 'acm'
    domain_name = None
    subject_alternate_names = None

    def __init__(self, domain_name, *, subject_alternate_names=None, **kwargs):
        super().__init__(**kwargs)
        self.domain_name = domain_name
        self.subject_alternate_names = subject_alternate_names

    @property
    def arn(self):
        if not self._data.get('CertificateArn'):
            raise ValueError('Certificate has not been initialized correctly. No ARN found.')

        return self._data.get('CertificateArn')

    @property
    def status(self):
        if not self._data.get('Status'):
            self.load()

        return self._data.get('Status')

    def create(self):
        kwargs = self.include_tags(
            DomainName=self.domain_name,
            ValidationMethod='DNS',
            KeyAlgorithm='RSA_2048',
        )
        if self.subject_alternate_names:
            kwargs.update({
                'SubjectAlternativeNames': self.subject_alternate_names,
            })

        self._data = self.client.request_certificate(**kwargs)

    def load(self):
        if self.arn:
            self._data = self.client.describe_certificate(
                CertificateArn=self.arn,
            ).get('Certificate')
        else:
            cert = type(self).find_by_domain(self.domain_name)
            cert.load()
            self._data = cert._data

    def validation_records(self, limit_to_domains=None):
        if not self._data.get('DomainValidationOptions'):
            self.load()

        names = []
        changes = []
        for item in self._data.get('DomainValidationOptions'):
            if limit_to_domains and item['DomainName'].lower() in limit_to_domains:
                continue

            if item['ValidationStatus'] == 'PENDING_VALIDATION':
                if item['ResourceRecord']['Name'] in names:
                    continue

                names.append(item['ResourceRecord']['Name'])

                changes.append(
                    Change(
                        Action='UPSERT',
                        ResourceRecordSet=ResourceRecord(
                            Name=item['ResourceRecord']['Name'],
                            Type='CNAME',
                            ResourceRecords=[
                                {
                                    'Value': item['ResourceRecord']['Value'],
                                },
                            ],
                        ),
                    )
                )

        return ChangeSet(Changes=changes) if changes else None

    def validate(self, *, wait=False):
        zone = Zone.find_by_domain(self.domain_name)
        zone.update(self.validation_records(), wait=wait)

        if wait:
            self.wait(
                'certificate_validated',
                CertificateArn=self.arn,
            )

    @classmethod
    def find_by_domain(cls, domain_name, **kwargs):
        self = cls(domain_name, **kwargs)

        for item in self.paginate('list_certificates', 'CertificateSummaryList'):
            if item['DomainName'] == domain_name or domain_name in item['SubjectAlternativeNameSummaries']:
                self._data = item
                return self

        return None
