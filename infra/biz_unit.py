from typing import List
from infra.landing_zone import ILandingZone
from aws_cdk import (
    core,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_s3 as s3,
)

class BisnessUnitConstruct(core.Construct):
  def __init__(self, scope:core.Construct, id:str, landing_zone:ILandingZone, unit_name:str, emr_ec2_role:iam.Role, **kwargs):
    super().__init__(scope, id, **kwargs)

    self.bucket = s3.Bucket(self,'Bucket',
      removal_policy= core.RemovalPolicy.DESTROY,
      bucket_name='{}.{}.{}'.format(
        landing_zone.zone_name,
        core.Stack.of(self).region,
        unit_name),
      lifecycle_rules=[
        s3.LifecycleRule(
          abort_incomplete_multipart_upload_after=core.Duration.days(7),
          expiration= core.Duration.days(30))
      ])
    
    # self.team_role = iam.Role(self,'TeamRole',
    #   assumed_by= iam.ServicePrincipal(service='ec2'),
    #   description= 'Group Role for '+unit_name)

    # # https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-emrfs-iam-roles.html
    # self.team_role.add_to_policy(
    #   iam.PolicyStatement(
    #     effect= iam.Effect.ALLOW,
    #     actions=['sts:AssumeRole'],
    #     principals=[iam.ArnPrincipal(emr_ec2_role.role_arn)]
    #   ))

    # emr_ec2_role.add_to_policy(
    #   iam.PolicyStatement(
    #     effect= iam.Effect.ALLOW,
    #     actions=['sts:AssumeRole'],
    #     principals=[iam.ArnPrincipal(self.team_role.role_arn)]
    #   ))

    # # Grant role read/write to the bucket
    # self.bucket.grant_read_write(self.team_role)
