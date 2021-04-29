from typing import List
import os.path as path
import jsii
from infra.landing_zone import ILandingZone
from infra.biz_unit import BisnessUnitConstruct
from infra.auth import DirectoryServicesConstruct
from aws_cdk import (
  core,
  aws_ec2 as ec2,
  aws_emr as emr,
  aws_iam as iam,
  aws_glue as g,
  aws_s3 as s3,
)

class EmrfsConstruct(core.Construct):
  def __init__(self, scope: core.Construct, id: str, landing_zone:ILandingZone, directory:DirectoryServicesConstruct, group_names:[List], job_flow_role:iam.Role, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)
    """
    Creates the business units from template.
    Then defines the Security Configuration with EMRFS Policy    
    """

    # Create the business units from template
    biz_units = {}
    for group in group_names:
      unit = BisnessUnitConstruct(self, 'BU_'+group,
        landing_zone=landing_zone,
        unit_name=group)

      biz_units[group] = unit

    # Business units can read each others data
    for owner in group_names:
      for peer in group_names:
        if owner == peer:
          continue

        biz_units[owner].bucket.grant_read(
          biz_units[peer].team_role)

    # Create policy to assume business unit roles
    # https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-emrfs-iam-roles.html
    emrfs_statement = iam.PolicyStatement(
      effect= iam.Effect.ALLOW,
      actions=['sts:AssumeRole'])
    
    for group in group_names:
      emrfs_statement.add_arn_principal(
        biz_units[group].team_role.role_arn)

    job_flow_role.assume_role_policy.add_statements(emrfs_statement)

    # Build out the security configuration
    # https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-create-security-configuration.html
    mappings = []
    for group in group_names:
      mappings.append({
        'Role': biz_units[group].team_role.role_arn,
        'IdentifierType':'Group',
        'Identifiers': [ group ]
      })

    self.security_configuration = emr.CfnSecurityConfiguration(self,'SecurityConfiguration',
      security_configuration= {
        "AuthorizationConfiguration": {
          "EmrFsConfiguration": {
            "RoleMappings": mappings
          }
        },
        "AuthenticationConfiguration":{
          "KerberosConfiguration":{
            "Provider":"ExternalKdc",
            "ExternalKdcConfiguration":{
              "KdcServerType":'Single',
              'AdminServer':directory.mad.name,
              'KdcServer':directory.mad.name,
              'AdIntegrationConfiguration':{
                'AdRealm': directory.mad.name,
                'AdServer': directory.mad.name,
                'AdDomain': directory.mad.name
              }
            }
            # "Provider": "ClusterDedicatedKdc",
            # "ClusterDedicatedKdcConfiguration":{
            #   "TicketLifetimeInHours": 24,
            #   "CrossRealmTrustConfiguration": {
            #     "Realm": "VIRTUAL.WORLD",
            #     "Domain": "virtual.world",
            #     "AdminServer": "virtual.world:749",
            #     "KdcServer": "virtual.world:88"
            #   }
            #}
          }
        }
      })
