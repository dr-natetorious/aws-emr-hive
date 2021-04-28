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
    
    self.admin = 'admin'
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

    document_name='Domain_Join_'+self.mad.ref
    self.domain_join_document = ssm.CfnDocument(self,'JoinDomainDocument',
      name= document_name,
      content={
        "schemaVersion": "1.0",
        "description": "Domain Join {}".format(self.mad.ref),
        "runtimeConfig": {
          "aws:domainJoin": {
            "properties": {
              "directoryId": self.mad.ref,
              "directoryName": "virtual.world",
              "dnsIpAddresses": [
                "10.100.18.34",
                "10.100.39.122",
              ]
            }
          }
        }
      })

    self.association = ssm.CfnAssociation(self,'JoinTagAssociation',
      association_name='joindomain_by_tags_'+self.mad.ref,
      name= document_name,
      targets= [
        ssm.CfnAssociation.TargetProperty(
          key='tag:domain',
          values=[landing_zone.zone_name])
      ])

    self.association.add_depends_on(self.domain_join_document)
