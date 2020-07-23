from aws_cdk import (
    core, 
    aws_ec2 as ec2, 
    aws_elasticloadbalancingv2 as elb, 
    aws_ecs as ecs,
    aws_servicediscovery as sd
)
import json

# Read config file
with open('./fargate_config.json') as f:
    config = json.load(f)


class FargateCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Set up VPC
        vpc = ec2.Vpc(self, 'CDKVPC',
            cidr=config['cidr']
        )

        # SG for ELB
        webSG = ec2.SecurityGroup(self, 'webSG',
            vpc=vpc,
            security_group_name='WebSG'
        )
        webSG.add_ingress_rule(
            peer=ec2.Peer.ipv4('0.0.0.0/0'),
            connection=ec2.Port.tcp(80)
        )
        webSG.add_ingress_rule(
            peer=ec2.Peer.ipv4('0.0.0.0/0'),
            connection=ec2.Port.tcp(443)
        )
        
        # Create ALB
        alb = elb.ApplicationLoadBalancer(self, 'webALB-public',
            vpc=vpc,
            load_balancer_name='webALB-public',
            security_group=webSG,
            internet_facing=True
        )

        # Add listener at port 80 with default action
        alblistener = alb.add_listener('webALB-Listener', 
            port=80, 
            open=True,
            default_action=elb.ListenerAction.fixed_response(
                status_code=200,
                content_type='text/plain',
                message_body='default action'
            )
        )

        # SG for ECS Fargate
        fargateSG = ec2.SecurityGroup(self, 'fargateSG',
            vpc=vpc,
            security_group_name='FargateSG'
        )
        fargateSG.add_ingress_rule(
            peer=webSG,
            connection=ec2.Port.tcp(80)
        )
        fargateSG.add_ingress_rule(
            peer=fargateSG,
            connection=ec2.Port.tcp(80)
        )

        # Create fargate cluster
        fargate_cluster = ecs.Cluster(self, 'FargateCluster',
            vpc=vpc,
            cluster_name='FargateCluster',
        )

        # Set up service discovery
        namespace = sd.PrivateDnsNamespace(self, 'PrivateDNSNamespace',
            name=config['service_discovery_namespace'],
            vpc=vpc
        )

        # Create fargate resources for each microservice
        for indx, s in enumerate(config['services']):

            # Create task definition and add the container from the repo
            task_definition = ecs.FargateTaskDefinition(self, 'ServiceTaskDefinition'+str(indx),
                cpu=1024,
                memory_limit_mib=2048
            )
            cont = task_definition.add_container('ServiceContainer'+str(indx),
                image=ecs.ContainerImage.from_registry(s['repo']),
                environment={"REGION": config['region']}
            )
            cont.add_port_mappings(
                ecs.PortMapping(
                    container_port=80,
                    host_port=80
                )
            )

            # Create service in private subnets
            service = ecs.FargateService(self, 'ServiceFargateService'+str(indx),
                task_definition=task_definition,
                assign_public_ip=False,
                security_group=fargateSG,
                vpc_subnets=ec2.SubnetSelection(subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE).subnets),
                cluster=fargate_cluster,
                desired_count=s['num_tasks']
            )
            service.enable_cloud_map(
                cloud_map_namespace=namespace,
                dns_record_type=sd.DnsRecordType.SRV,
                name=s['service_discovery_service_name']
            )

            # Set up ALB target group and set Fargate service as target
            target_group = elb.ApplicationTargetGroup(self, 'ServiceTargetGroup'+str(indx),
                port=80,
                vpc=vpc,
                target_type=elb.TargetType.IP,
                target_group_name=s['service_name']+'TargetGroup',
                targets=[service.load_balancer_target(
                    container_name='ServiceContainer'+str(indx),
                    container_port=80
                )]
            )

            # Add the path pattern rule for the listener
            alblistenerrule = elb.ApplicationListenerRule(self, 'ListenerRule'+str(indx),
                path_pattern=s['alb_routing_path'],
                priority=indx+1,
                listener=alblistener,
                target_groups=[target_group]
            )