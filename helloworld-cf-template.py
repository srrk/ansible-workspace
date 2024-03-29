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

ApplicationPort = 3000
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

# Planting application startup script.
ud = Base64(Join('\n',[
    "#!/bin/bash",
    "sudo yum install --enablerepo=epel -y nodejs",
    "wget http://bit.ly/2vESNuc -O /home/ec2-user/helloworld.js",
    "wget http://bit.ly/2vVvT18 -O /etc/init/helloworld.conf",
    "start helloworld"
]))

t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-a4c7edb2",
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud,
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