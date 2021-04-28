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

src_root_dir = path.join(path.dirname(__file__),"../..")
services = {
  9870: 'HDFS Name Name',
  18080: 'Spark History',
  8888: 'Hue',
  9443: 'JupyterHub',
  8088: 'Resource Manager',
  9864: 'HDFS DataNode',
  8042: 'Node Manager',
  443: 'Https',
  80: 'Http'
}

class HadoopConstruct(core.Construct):
  """
  Configure the Hadoop management
  """
  @property
  def landing_zone(self)->ILandingZone:
    return self.__landing_zone

  def __init__(self, scope: core.Construct, id: str, landing_zone:ILandingZone, directory:DirectoryServicesConstruct, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)
    self.__landing_zone = landing_zone

    # Configure the security groups
    self.security_group = ec2.SecurityGroup(self,'SecurityGroup',
      vpc=landing_zone.networking.vpc,
      allow_all_outbound=True,
      description='HadoopConstruct Security Group',
      security_group_name='hadoop-mapreduce-group')

    for port in services.keys():
      self.security_group.add_ingress_rule(
        peer = ec2.Peer.any_ipv4(),
        connection= ec2.Port(
          protocol= ec2.Protocol.TCP,
          from_port=port, to_port=port,
          string_representation=services[port])
      )

    self.security_group.add_ingress_rule(
      peer = ec2.Peer.any_ipv4(),
      connection= ec2.Port(
        protocol= ec2.Protocol.UDP,
        from_port=0, to_port=65535,
        string_representation='Allow All UDP Traffic')
    )

    self.security_group.add_ingress_rule(
      peer = ec2.Peer.any_ipv4(),
      connection= ec2.Port(
        protocol= ec2.Protocol.TCP,
        from_port=0, to_port=65535,
        string_representation='Allow All TCP Traffic')
    )

    # Setup roles...    
    self.jobFlowRole = iam.Role(self,'JobFlowRole', assumed_by=iam.ServicePrincipal(service='ec2.amazonaws.com'), 
      managed_policies=[
        iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonElasticMapReduceforEC2Role'),
      ]
    )

    profile_name='jobflowprofile@{}-{}'.format(landing_zone.zone_name, core.Stack.of(self).region)
    job_flow_instance_profile = iam.CfnInstanceProfile(self,'JobFlowInstanceProfile',
      instance_profile_name=profile_name,
      roles=[self.jobFlowRole.role_name])

    serviceRole = iam.Role(self,'ServiceRole', assumed_by=iam.ServicePrincipal(service='elasticmapreduce.amazonaws.com'),
      managed_policies=[
        iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonElasticMapReduceRole')
      ]
    )

    self.database = g.Database(self,'GlueStore',
      database_name='demo-database')

    self.bucket = s3.Bucket(self,'LogBucket',
      removal_policy= core.RemovalPolicy.DESTROY)

    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-elasticmapreduce-instancefleetconfig.html
    self.cluster = emr.CfnCluster(self,'MapRed',
      name='HadoopCluster',
      job_flow_role=profile_name, #'EMR_EC2_DefaultRole',
      service_role=serviceRole.role_name,
      log_uri='s3://'+self.bucket.bucket_name+'/logs',
      release_label='emr-6.2.0',
      applications=[
        emr.CfnCluster.ApplicationProperty(name='Spark'),
        emr.CfnCluster.ApplicationProperty(name='Presto'),
        emr.CfnCluster.ApplicationProperty(name='Hue'),
        emr.CfnCluster.ApplicationProperty(name='Hive'),
        emr.CfnCluster.ApplicationProperty(name='JupyterHub'),
      ],
      configurations= [
        emr.CfnCluster.ConfigurationProperty(
          classification='spark-hive-site',
          configuration_properties={
            'hive.metastore.client.factory.class':'com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory'
          }),
         emr.CfnCluster.ConfigurationProperty(
          classification='hive-site',
          configuration_properties={
            'hive.metastore.client.factory.class':'com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory',
            'aws.glue.partition.num.segments':'10', #1 to 10; (default=5)
            'hive.metastore.schema.verification': 'false',
          })
      ],
      # kerberos_attributes= emr.CfnCluster.KerberosAttributesProperty(
      #   kdc_admin_password=directory.password,
      #   realm= directory.mad.name,
      #   ad_domain_join_password=directory.password,
      #   ad_domain_join_user= directory.username
      # ),
      managed_scaling_policy= emr.CfnCluster.ManagedScalingPolicyProperty(
        compute_limits=emr.CfnCluster.ComputeLimitsProperty(
          minimum_capacity_units=1,
          maximum_capacity_units=25,
          unit_type='InstanceFleetUnits'
        )
      ),
      instances= emr.CfnCluster.JobFlowInstancesConfigProperty(
        #hadoop_version='2.4.0',
        termination_protected=False,
        master_instance_fleet= emr.CfnCluster.InstanceFleetConfigProperty(
          target_spot_capacity=1,
          instance_type_configs= [
            emr.CfnCluster.InstanceTypeConfigProperty(
              instance_type='m5.xlarge',
            )
        ]),
        core_instance_fleet= emr.CfnCluster.InstanceFleetConfigProperty(
          target_spot_capacity=1,
          instance_type_configs=[
            emr.CfnCluster.InstanceTypeConfigProperty(
              instance_type='m5.xlarge',
              ebs_configuration= emr.CfnCluster.EbsConfigurationProperty(
                ebs_block_device_configs=[
                  emr.CfnCluster.EbsBlockDeviceConfigProperty(
                  volume_specification=emr.CfnCluster.VolumeSpecificationProperty(
                    size_in_gb=50,
                    volume_type='gp2'))
                ]
              )
          )
        ]),
        additional_master_security_groups=[self.security_group.security_group_id],
        additional_slave_security_groups=[self.security_group.security_group_id],
        ec2_subnet_ids=[net.subnet_id for net in landing_zone.networking.vpc._select_subnet_objects(subnet_group_name='Hadoop')],
      )
    )

    self.cluster.add_depends_on(job_flow_instance_profile)

  def add_business_unit(self, team_name:str)->BisnessUnitConstruct:
    bizunit = BisnessUnitConstruct(self, 'BU_'+team_name,
      landing_zone=self.landing_zone,
      unit_name=team_name,
      emr_ec2_role=self.jobFlowRole)
