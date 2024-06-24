
import json

from awacs.aws import PolicyDocument

from ..base import Boto3Base
from .constants import generic_assume_policy


class IAMBase(Boto3Base):
    _service = 'iam'
    _data = None


class User(IAMBase):
    username = None

    def __init__(self, username, **kwargs):
        super().__init__(**kwargs)
        self.username = username

    def create(self, *, wait=False):
        kwargs = self.include_tags(UserName=self.username)
        self._data = self.client.create_user(**kwargs).get('User')

        if wait:
            self.wait(
                'user_exists',
                UserName=self.username,
            )

    @classmethod
    def find_by_name(cls, username, **kwargs):
        self = cls(username, **kwargs)
        try:
            self.load()
            return self
        except self.client.exceptions.NoSuchEntityException:
            return None

    def attach_policy(self, policy):
        self.client.attach_user_policy(
            UserName=self.username,
            PolicyArn=policy.arn,
        )

    def create_access_key(self):
        kwargs = self.init_args
        kwargs.pop('tags')  # AccessKey does not support tags

        key = AccessKey(self, **kwargs)
        key.create()
        return key

    def load(self):
        self._data = self.client.get_user(UserName=self.username)


class AccessKey(IAMBase):
    owner = None
    _access_key_id = None
    _secret_access_key = None

    def __init__(self, owner, *, access_key_id=None, secret_access_key=None, **kwargs):
        if kwargs.get('tags'):
            raise ValueError('AccessKey does not support tags')

        super().__init__(**kwargs)
        self.owner = owner

        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key

    @property
    def arn(self):
        raise AttributeError('AccessKey does not have an ARN!')

    def create(self):
        self._data = self.client.create_access_key(
            UserName=self.owner.username,
        ).get('AccessKey')

    @property
    def access_key_id(self):
        if self._access_key_id is None:
            self._access_key_id = self._data['AccessKeyId']

        return self._access_key_id

    @access_key_id.setter
    def access_key_id(self, value):
        self._access_key_id = value

    @property
    def secret_access_key(self):
        if self._secret_access_key is None:
            self._secret_access_key = self._data['SecretAccessKey']

        return self._secret_access_key

    @secret_access_key.setter
    def secret_access_key(self, value):
        self._secret_access_key = value

    def write_locally(self, file):
        try:
            self._write_locally(file)

        except AttributeError:
            with open(file, 'w', encoding='utf-8') as filehandle:
                self._write_locally(filehandle)

    def _write_locally(self, filehandle):
        filehandle.writelines([
            f'export AWS_ACCESS_KEY_ID="{self.access_key_id}"\n',
            f'export AWS_SECRET_ACCESS_KEY="{self.secret_access_key}"\n',
        ])


class Policy(IAMBase):
    policy_name = None
    policy = None

    def __init__(self, policy_name, policy, **kwargs):
        super().__init__(**kwargs)
        self.policy_name = policy_name
        self.policy = policy

    def create(self, *, wait=False):
        kwargs = self.include_tags(
            PolicyName=self.policy_name,
            PolicyDocument=self.policy_string,
        )
        self._data = self.client.create_policy(**kwargs).get('Policy')

        if wait:
            self.wait(
                'policy_exists',
                PolicyArn=self.arn,
            )

    @property
    def policy_string(self):
        if isinstance(self.policy, PolicyDocument):
            return self.policy.to_json()

        if isinstance(self.policy, str):
            return self.policy

        return json.dumps(self.policy)

    def cleanup_versions(self):
        raise NotImplementedError('TODO: implement version cleanup for policies')


class Role(IAMBase):
    role_name = None
    _assume_policy = None

    def __init__(self, role_name, *, assume_policy=None, **kwargs):
        super().__init__(**kwargs)
        self.role_name = role_name
        self._assume_policy = assume_policy

    @property
    def assume_policy(self):
        if self._assume_policy is None:
            self._assume_policy = generic_assume_policy()

        return self._assume_policy

    @assume_policy.setter
    def assume_policy(self, value):
        self._assume_policy = value

    def create(self, wait=False):
        kwargs = self.include_tags(
            RoleName=self.role_name,
            AssumePolicyDocument=self.assume_policy.policy_string,
        )
        self._data = self.client.create_role(**kwargs).get('Role')

        if wait:
            self.wait(
                'role_exists',
                RoleName=self.role_name,
            )

    def attach_policy(self, policy):
        self.client.put_role_policy(
            RoleName=self.role_name,
            PolicyName=policy.policy_name,
            PolicyDocument=policy.policy_string,
        )


class InstanceProfile(IAMBase):
    profile_name = None

    def __init__(self, profile_name, **kwargs):
        super().__init__(**kwargs)
        self.profile_name = profile_name

    def create(self, *, wait=False):
        kwargs = self.include_tags(
            InstanceProfileName=self.profile_name,
        )
        self._data = self.client.create_instance_profile(**kwargs).get('InstanceProfile')

        if wait:
            self.wait(
                'instance_profile_exists',
                InstanceProfileName=self.profile_name,
            )
