
from awacs.aws import (
    Action,
    Allow,
    PolicyDocument,
    Principal,
    Statement,
)
from awacs.sts import AssumeRole


def generic_assume_policy():
    from .core import Policy  # pylint: disable=import-outside-top-level

    return Policy(
        policy_name='assume-policy',
        policy=PolicyDocument(
            Version='2012-10-17',
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[AssumeRole],
                    Principal=Principle(
                        'Service',
                        [
                            'apigateway.amazonaws.com',
                            'events.amazonaws.com',
                            'lambda.amazonaws.com',
                        ]
                    ),
                )
            ],
        )
   )
