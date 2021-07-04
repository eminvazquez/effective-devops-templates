"""CloudFormation template."""

from troposphere import (
  Base64,
  ec2,
  GetAtt,
  Join,
  Output,
  Parameter,
  Ref,
  Template,
)
from ipaddress import ip_network
from requests import get

ApplicationName = "helloworld"
ApplicationPort = "3000"
GithubAccount = "eminvazquez"
GithubAnsibleURL = "https://github.com/{}/effective-devops-ansible".format(GithubAccount)
AnsiblePullCmd = "/usr/bin/ansible-pull -U {} {}.yml -i localhost".format(GithubAnsibleURL, ApplicationName)
PublicCidrIp = str(ip_network(get('https://api.ipify.org').text))

t = Template()

t.set_description("Effective DevOps With AWS: HelloWorld web application")

t.add_parameter(Parameter(
  "KeyPair",
  Description="Name of an existing EC2 KeyPair to SSH",
  Type="AWS::EC2::KeyPair::KeyName",
  ConstraintDescription="Must be the name of an existing EC2 KeyPair."
))

t.add_resource(ec2.SecurityGroup(
  "SecurityGroup",
  GroupDescription="Allow SSH and TCP/{} access.".format(ApplicationPort),
  SecurityGroupIngress=[
    ec2.SecurityGroupRule(
      IpProtocol="tcp",
      FromPort="22",
      ToPort="22",
      CidrIp=PublicCidrIp
    ),
    ec2.SecurityGroupRule(
      IpProtocol="tcp",
      FromPort=ApplicationPort,
      ToPort=ApplicationPort,
      CidrIp="0.0.0.0/0"
    ),
  ],
))

ud = Base64(Join('\n', [
  "#!/bin/bash",
  "sudo yum install --enablerepo=epel -y git",
  "pip install ansible",
  AnsiblePullCmd,
  "echo '*/10 * * * * {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCmd)
]))

t.add_resource(ec2.Instance(
  "instance",
  ImageId="ami-cfe4b2b0",
  InstanceType="t2.micro",
  SecurityGroups=[Ref("SecurityGroup")],
  KeyName=Ref("KeyPair"),
  UserData=ud,
))

t.add_output(Output(
  "InstancePublicIp",
  Description="Public IP of our instance.",
  Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
  "WebUrl",
  Description="Application endpoint",
  Value=Join("", [
    "http://",
    GetAtt("instance", "PublicDnsName"),
    ":",
    ApplicationPort
  ]),
))

print(t.to_json())