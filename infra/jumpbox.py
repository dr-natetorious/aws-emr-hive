from typing import List
from infra.landing_zone import ILandingZone
from infra.auth import DirectoryServicesConstruct
from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_directoryservice as ds,
)

class JumpBoxConstruct(core.Construct):
  def __init__(self, scope:core.Construct, id:str, landing_zone:ILandingZone, directory:DirectoryServicesConstruct, **kwargs):
    """
    Configure Dns Resolver
    """
    super().__init__(scope,id, **kwargs)

    self.security_group = ec2.SecurityGroup(self,'SecurityGroup',
      description='JumpBox Security Group', 
      vpc= landing_zone.vpc,
      allow_all_outbound=True)

    role = iam.Role(self,'Role',
      assumed_by=iam.ServicePrincipal(
        service='ec2',
        region=core.Stack.of(self).region),
      managed_policies=[
        iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMDirectoryServiceAccess'),
      ])

    self.instance = ec2.Instance(self,'JumpBox',
      role= role,
      vpc= landing_zone.vpc,
      instance_type=ec2.InstanceType.of(
        instance_class= ec2.InstanceClass.BURSTABLE3,
        instance_size=ec2.InstanceSize.SMALL),
      allow_all_outbound=True,
      user_data_causes_replacement=True,
      security_group= self.security_group,
      vpc_subnets= ec2.SubnetSelection(subnet_group_name='Public'),
      machine_image= ec2.MachineImage.generic_windows(ami_map={
        'eu-west-1': 'ami-03b9a7c8f0fc1808e',
      }))

    # self.association = ssm.CfnAssociation(self,'DomainJoinAssociation',
    #   document_version='LATEST',
    #   name= directory.auto_join_domain.ref,
    #   instance_id= self.instance.instance_id)


    
