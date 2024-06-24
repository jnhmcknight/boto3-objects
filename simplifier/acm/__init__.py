

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
        return self._data.get('CertificateArn')

    def create(self):
        kwargs = self.include_tags(
            DomainName=self.domain_name,
            ValidationMethod='DNS',
            KeyAlgorithm='RSA_2048',
        )
        if self.subject_alternate_names:
            kwargs.update({
                'SubjectAlternativeNameSummaries': self.subject_alternate_names,
            })

        self._data = self.client.request_certificate(**kwargs)

    def load(self):
        if self.arn:
            self._data = self.client.describe_certificate(
                CertificateArn=self.arn,
            )
        else:
            cert = type(self).find_by_domain(self.domain_name)
            cert.load()
            self._data = cert._data

    def validation_records(self, limit_to_domains=None):
        if not self._data.get('DomainValidationOptions'):
            self.load()

        changes = []
        for item in self._data.get('DomainValidationOptions'):
            if limit_to_domains and item['DomainName'].lower() in limit_to_domains:
                continue

            if item['ValidationStatus'] == 'PENDING_VALIDATION':
                changes.append(
                    Change(
                        Action='UPSERT',
                        ResourceRecordSet=ResourceRecord(
                            Name=item['DomainName'],
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
        zone.update(self.validation_records())

        if wait:
            self.wait(
                'certificate_validated',
                CertificateArn=self.arn,
            )

    @classmethod
    def find_by_domain(self, domain_name, **kwargs):
        cert = Certificate(domain_name, **kwargs)

        for item in cert.paginate('list_certificates', 'CertificateSummaryList'):
            if item['DomainName'] == domain_name or domain_name in item['SubjectAlternativeNameSummaries']:
                cert._data = item
                return cert

        raise ValueError('No cert with that domain name could be found')
