"""Generating CloudFormation Template"""
from ipaddress import ip_network
from ipify import get_ip

from troposphere import (
    Base64,
    ec2,
    GetAtt,
    Join,
    Output,
    Parameter,
    Ref,
    Template
)

from troposphere.iam import (
    InstanceProfile,
    PolicyType as IAMPolicy,
    Role,
)

from awacs.aws import (
    Action,
    Allow,
    Policy,
    Principal,
    Statement,
)

from awacs.sts import AssumeRole

ApplicationName = "jenkins"
ApplicationPort = 8080
GithubAccount = "srrk"
GithubAnsibleURL = "https://github.com/{}/ansible-workspace".format(GithubAccount)
AnsiblePullCommand = \
    "/usr/local/bin/ansible-pull -U {} {}.yml -i localhost --sleep 60".format(
        GithubAnsibleURL,
        ApplicationName
    )
PublicCidrIp = str(ip_network(get_ip()))

t = Template()
t.add_description("Effective Devops in AWS : HelloWorld Web Application")
t.add_parameter(Parameter(
    "KeyPair",
    Description="Name of an existing EC2 keypair to SSH",
    Type="AWS::EC2::KeyPair::KeyName",
    ConstraintDescription="must be the name of an existing EC2 keypair"
))
t.add_resource(ec2.SecurityGroup(
    "SecurityGroup",
    GroupDescription="Allow SSH and TCP/{}".format(ApplicationPort),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp=PublicCidrIp,
        ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=ApplicationPort,
            ToPort=ApplicationPort,
            CidrIp="0.0.0.0/0",
        )
    ]
))

# Planting application startup script for ansible-pull
ud = Base64(Join('\n',[
    "#!/bin/bash",
    "yum install --enablerepo=epel -y git",
    "yum install --enablerepo=epel -y libffi-devel openssl-devel gcc",
    "pip install --upgrade setuptools",
    "pip install ansible",
    AnsiblePullCommand,
    "echo '*/10 * * * * {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCommand)
]))

# Add the role for creating Role & 'Instance Profile'
t.add_resource(Role(
    "Role",
    AssumeRolePolicyDocument=Policy(
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service",["ec2.amazonaws.com"]),
            )
        ]
    )
))

t.add_resource(InstanceProfile(
    "InstanceProfile",
    Path="/",
    Roles=[Ref("Role")]
))

t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-a4c7edb2",
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud,
    IamInstanceProfile=Ref("InstanceProfile"),
))

t.add_output(Output(
    "InstancePublicIp",
    Description="Public Ip of our Instance.",
    Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
    "Weburl",
    Description="Application Endpoint",
    Value=Join("",[
        "http://",GetAtt("instance","PublicDnsName"),
        ":", ApplicationPort
    ])
))

# Generate json output.
print t.to_json()