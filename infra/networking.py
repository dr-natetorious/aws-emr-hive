#!/usr/bin/env python3
import os.path
from typing import List
from aws_cdk.core import App, Stack, Environment, Construct, NestedStack
from infra.backup import BackupStrategyConstruct
from infra.emr import HadoopConstruct
from infra.vpce import VpcEndpointsForAWSServices
from infra.landing_zone import ILandingZone
from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ssm as ssm,
)

src_root_dir = os.path.join(os.path.dirname(__file__))

class NetworkingLayer(core.Construct):
  """
  Configure the networking layer
  """
  def __init__(self, scope: core.Construct, id: str,cidr:str,subnet_configuration:List[ec2.SubnetConfiguration], **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    self.vpc = ec2.Vpc(self,'Network',
      cidr=cidr,
      enable_dns_hostnames=True,
      enable_dns_support=True,
      max_azs=2,
      nat_gateways=1,
      subnet_configuration=subnet_configuration)

class LandingZone(ILandingZone):
  """
  Define a deployment instance
  """
  def __init__(self, scope:Construct, id:str, **kwargs)->None:
    super().__init__(scope, id, **kwargs)
    core.Tags.of(self).add('zone_name',self.zone_name)

    # Deploy the VPC and networking components
    self.networking = NetworkingLayer(self,self.zone_name,
      cidr=self.cidr_block,
      subnet_configuration=self.subnet_configuration)

    # Automatically backup anything with backup-tags
    self.backup_policy = BackupStrategyConstruct(self,'Backup', landing_zone=self)

    # Support AWS services within isolated subnets
    self.vpc_endpoints = VpcEndpointsForAWSServices(self,'Endpoints',vpc=self.vpc)
    self.vpc_endpoints.add_s3_and_dynamodb()
    self.vpc_endpoints.add_ssm_support()
    self.vpc_endpoints.add_emr_support()

  @property
  def cidr_block(self)->str:
    raise NotImplementedError()

  @property
  def zone_name(self)->str:
    raise NotImplementedError()

  @property
  def subnet_configuration(self)->List[ec2.SubnetConfiguration]:
    raise NotImplementedError()

  @property
  def vpc(self)->ec2.IVpc:
    return self.networking.vpc

class EuroMapRed(LandingZone):
  """
  Define our custom deployment within Ireland.
  """
  def __init__(self, scope:Construct, id:str, **kwargs)->None:
    super().__init__(scope, id, **kwargs)    

    self.emr = HadoopConstruct(self,'Analytics', landing_zone=self)

  @property
  def cidr_block(self)->str:
    return '10.100.0.0/16'

  @property
  def zone_name(self)->str:
    return 'euro-mapred'

  @property
  def subnet_configuration(self)->List[ec2.SubnetConfiguration]:
    return [
      ec2.SubnetConfiguration(name='Public',subnet_type= ec2.SubnetType.PUBLIC, cidr_mask=24),
      ec2.SubnetConfiguration(name='Hadoop',subnet_type= ec2.SubnetType.PRIVATE, cidr_mask=20),
    ]
