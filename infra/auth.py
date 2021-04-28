from typing import List
from infra.landing_zone import ILandingZone
from aws_cdk import (
    core,
    aws_ssm as ssm,
    aws_directoryservice as ds,
)

class DirectoryServicesConstruct(core.Construct):
  def __init__(self, scope:core.Construct, id:str, landing_zone:ILandingZone, **kwargs):
    """
    Configure Dns Resolver
    """
    super().__init__(scope,id, **kwargs)
    
    self.username= 'admin'
    self.password = 'I-l1K3-74(oz'
    self.mad = ds.CfnMicrosoftAD(self,'ActiveDirectory',
      name='virtual.world',
      password= self.password,
      short_name='virtualworld',
      enable_sso=False,
      edition= 'Standard',
      vpc_settings= ds.CfnMicrosoftAD.VpcSettingsProperty(
        vpc_id= landing_zone.vpc.vpc_id,
        subnet_ids= landing_zone.vpc.select_subnets(subnet_group_name='Hadoop').subnet_ids
      ))

    self.auto_join_domain = ssm.CfnDocument(self,'DomainJoinDocument',
      name='awsconfig_DomainJoin_'+self.mad.ref,
      content={
        "schemaVersion": "1.0",
        "description": "Automatic Domain Join Configuration created by EC2 Console.",
        "runtimeConfig": {
          "aws:domainJoin": {
            "properties": {
              "directoryId": self.mad.ref,
              "directoryName": "virtual.world",
              # "dnsIpAddresses": [
              #   "10.0.2.60",
              #   "10.0.2.9"
              # ]
            }
          }
        }
      })

    # self.association = ssm.CfnAssociation(self,'DomainJoinAssociation',
    #   association_name='Autojoin machines by tag to '+self.mad.ref,
    #   # document_version='LATEST',
    #   name= self.auto_join_domain.ref,
    #   targets= [
    #     ssm.CfnAssociation.TargetProperty(
    #       key='domain',
    #       values=[landing_zone.zone_name])
    #   ])
