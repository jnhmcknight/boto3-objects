
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import typing as t

from ..base import Boto3Base


class PolicyType(Enum):
    MANAGED = 'managed'
    CUSTOM = 'custom'


class HTTPMethod(Enum):
    DELETE = 'DELETE'
    GET = 'GET'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'
    POST = 'POST'
    PUT = 'PUT'

    @property
    def ALL(self) -> t.List['HTTPMethod']:
        return [
            self.DELETE,
            self.GET,
            self.HEAD,
            self.OPTIONS,
            self.PATCH,
            self.POST,
            self.PUT,
        ]


class FrameOption(Enum):
    DENY = 'DENY'
    SAMEORIGIN = 'SAMEORIGIN'


class ReferrerOption(Enum):
    NO_REFERRER = 'no-referrer'
    NO_REFERRER_WHEN_DOWNGRADE = 'no-referrer-when-downgrade'
    ORIGIN = 'origin'
    ORIGIN_WHEN_CROSS_ORIGIN = 'origin-when-cross-origin'
    SAME_ORIGIN = 'same-origin'
    STRICT_ORIGIN = 'strict-origin'
    STRICT_ORIGIN_WHEN_CROSS_ORIGIN = 'strict-origin-when-cross-origin'
    UNSAFE_URL = 'unsafe-url'


@dataclass(kw_only=True)
class StringItemsArray:
    Items: t.List[str] = None

    @property
    def quantity(self) -> int:
        return len(self.Items) if isinstance(self.Items, list) else 0


@dataclass(kw_only=True)
class HTTPMethodItemsArray(StringItemsArray):
    Items: t.List[HTTPMethod] = None


@dataclass(kw_only=True)
class CorsConfig:
    AccessControlAllowOrigins: StringItemsArray = None
    AccessControlAllowHeaders: StringItemsArray = None
    AccessControlAllowMethods: HTTPMethodItemsArray = None
    AccessControlAllowCredentials: bool = False
    AccessControlExposeHeaders: StringItemsArray = None
    AccessControlMaxAgeSec: int = None
    OriginOverride: bool = False


@dataclass(kw_only=True)
class OverridableMixin:
    Override: bool = False


@dataclass(kw_only=True)
class ContentTypeOptions(OverridableMixin):
    pass


@dataclass(kw_only=True)
class CSP(OverridableMixin):
    ContentSecurityPolicy: str = None


@dataclass(kw_only=True)
class FrameOptions(OverridableMixin):
    FrameOption: FrameOption = None


@dataclass(kw_only=True)
class ReferrerPolicy(OverridableMixin):
    ReferrerPolicy: ReferrerOption = None


@dataclass(kw_only=True)
class StrictTransportSecurity(OverridableMixin):
    IncludeSubdomains: bool = True
    Preload: bool = False
    AccessControlMaxAgeSec: int = None


@dataclass(kw_only=True)
class XssProtection(OverridableMixin):
    Protection: bool = True
    ModeBlock: bool = True
    ReportUri: str = None


@dataclass(kw_only=True)
class SecurityHeadersConfig:
    ContentTypeOptions: ContentTypeOptions = None
    ContentSecurityPolicy: CSP = None
    FrameOptions: FrameOptions = None
    ReferrerPolicy: ReferrerPolicy = None
    StrictTransportSecurity: StrictTransportSecurity = None
    XSSProtection: XssProtection = None


class Policy(Boto3Base):
    _service: str = 'cloudfront'

    id: str = None
    etag: str = None
    type: PolicyType = None
    policy: t.Dict[str, any] = None

    def paginate(self, paginate_func, *result_keys, **kwargs):
        marker = kwargs.get('Marker')
        next_marker = None
        results = paginate_func(**kwargs)

        for key in result_keys:
            next_marker = results.get('NextMarker')
            results = results.get(key, [])

        for item in results:
            yield item

        if next_marker and next_marker != marker:
            print(f'pagination: {marker} -> {next_marker}')
            yield self.paginate(paginate_func, *result_keys, Marker=next_marker, **kwargs)


class OriginPolicy(Policy):
    pass


class RequestPolicy(Policy):
    pass


class ResponsePolicy(Policy):

    def __init__(self, name, *,
        policy=None,
        cors=None,
        content_type_options=None,
        csp=None,
        frame_options=None,
        referrer_policy=None,
        strict_transport_security=None,
    ):
        self.policy = policy or {}
        self.name = name
        if cors is not None:
            self.cors = cors
        if content_type_options is not None:
            self.content_type_options = content_type_options
        if csp is not None:
            self.csp = csp
        if frame_options is not None:
            self.frame_options = frame_options
        if referrer_policy is not None:
            self.referrer_policy = referrer_policy
        if strict_transport_security is not None:
            self.strict_transport_security = strict_transport_security

    @property
    def name(self):
        return self.policy.get('Name', None)

    @name.setter
    def name(self, value):
        if value is None:
            raise ValueError('Policy requires a name')
        else:
            self.policy['Name'] = value

    @property
    def cors(self):
        return self.policy.get('CorsConfig', None)

    @cors.setter
    def cors(self, value):
        if value is None:
            self.policy.pop('CorsConfig', None)
        else:
            self.policy['CorsConfig'] = value

    @property
    def csp(self):
        return self.policy.get('SecurityHeadersConfig', {}).get('ContentSecurityPolicy', None)

    @csp.setter
    def csp(self, value):
        if value is None:
            self.policy.get('SecurityHeadersConfig', {}).pop('ContentSecurityPolicy', None)
        else:
            if 'SecurityHeadersConfig' not in self.policy:
                self.policy.update({'SecurityHeadersConfig': {}})
            self.policy['SecurityHeadersConfig'].update({'ContentSecurityPolicy': value})

    @property
    def frame_options(self):
        return self.policy.get('SecurityHeadersConfig', {}).get('FrameOptions', None)

    @frame_options.setter
    def frame_options(self, value):
        if value is None:
            self.policy.get('SecurityHeadersConfig', {}).pop('FrameOptions', None)
        else:
            if 'SecurityHeadersConfig' not in self.policy:
                self.policy.update({'SecurityHeadersConfig': {}})
            self.policy['SecurityHeadersConfig'].update({'FrameOptions': value})

    @property
    def referrer_policy(self):
        return self.policy.get('SecurityHeadersConfig', {}).get('ReferrerPolicy', None)

    @referrer_policy.setter
    def referrer_policy(self, value):
        if value is None:
            self.policy.get('SecurityHeadersConfig', {}).pop('ReferrerPolicy', None)
        else:
            if 'SecurityHeadersConfig' not in self.policy:
                self.policy.update({'SecurityHeadersConfig': {}})
            self.policy['SecurityHeadersConfig'].update({'ReferrerPolicy': value})

    @property
    def content_type_options(self):
        return self.policy.get('SecurityHeadersConfig', {}).get('ContentTypeOptions', None)

    @content_type_options.setter
    def content_type_options(self, value):
        if value is None:
            self.policy.get('SecurityHeadersConfig', {}).pop('ContentTypeOptions', None)
        else:
            if 'SecurityHeadersConfig' not in self.policy:
                self.policy.update({'SecurityHeadersConfig': {}})
            self.policy['SecurityHeadersConfig'].update({'ContentTypeOptions': value})

    @property
    def strict_transport_security(self):
        return self.policy.get('SecurityHeadersConfig', {}).get('StrictTransportSecurity', None)

    @strict_transport_security.setter
    def strict_transport_security(self, value):
        if value is None:
            self.policy.get('SecurityHeadersConfig', {}).pop('StrictTransportSecurity', None)
        else:
            if 'SecurityHeadersConfig' not in self.policy:
                self.policy.update({'SecurityHeadersConfig': {}})
            self.policy['SecurityHeadersConfig'].update({'StrictTransportSecurity': value})

    @classmethod
    def find_by_name(cls, name):
        self = cls(name)
        for policy in self.paginate(self.client.list_response_headers_policies, 'ResponseHeadersPolicyList', 'Items'):
            check = policy['ResponseHeadersPolicy']
            if check.get('ResponseHeadersPolicyConfig', {}).get('Name') == name:
                self.type = policy['Type']

                self.id = check['Id']
                self.policy = check['ResponseHeadersPolicyConfig']
                return self

        return None

    @classmethod
    def find_by_id(cls, id_):
        self = cls(id_)
        try:
            policy = self.client.get_response_headers_policy(
                Id=id_,
            )

            self.type = policy['Type']

            check = policy['ResponseHeadersPolicy']
            self.etag = policy['ETag']
            self.id = check['Id']
            self.policy = check['ResponseHeadersPolicyConfig']
            return self

        except self.client.exceptions.NoSuchResponseHeadersPolicy:
            return None

    def create(self):
        self.policy['Name'] = self.name
        resp = self.client.create_response_headers_policy(
            ResponseHeadersPolicyConfig=self.policy,
        )
        self.id = resp['ResponseHeadersPolicy']['Id']
        self.etag = resp['ETag']

    def update(self):
        resp = self.client.create_response_headers_policy(
            Id=self.id,
            IfMatch=self.etag,
            ResponseHeadersPolicyConfig=self.policy,
        )
        self.id = resp['ResponseHeadersPolicy']['Id']
