from aws_cdk import (
    core, 
    aws_ec2 as ec2, 
    aws_elasticloadbalancingv2 as elb, 
    aws_route53 as r53, 
    aws_route53_targets as alias, 
    aws_rds as rds, 
    aws_secretsmanager as sm,
    aws_certificatemanager as acm,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_ecr as ecr,
)
import sys
sys.path.insert(1, '../')
import vars


class FargateCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, 'CDKVPC',
            cidr=vars.cidr
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

        




        # SG for ECS Fargate
        fargateSG = ec2.SecurityGroup(self, 'fargateSG',
            vpc=vpc,
            security_group_name='FargateSG'
        )
        fargateSG.add_ingress_rule(
            peer=webSG,
            connection=ec2.Port.tcp(80)
        )

        # Create fargate cluster
        fargate_cluster = ecs.Cluster(self, 'FargateCluster',
            vpc=vpc,
            cluster_name='FargateCluster',
        )

        # Microservice 1
        service1_ecr_repo = ecr.Repository.from_repository_name(self, 'Service1Repo', vars.ecr_repos[0])
        task_definition_1 = ecs.FargateTaskDefinition(self, 'Service1TaskDefinition',
            cpu=1024,
            memory_limit_mib=2048
        )
        service1_container = task_definition_1.add_container('Service1Container',
            image=ecs.ContainerImage.from_ecr_repository(service1_ecr_repo),
            environment={"region": vars.region}
        )
        service1_container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                host_port=80
            )
        )

        service1_fargateservice = ecs.FargateService(self, 'Service1FargateService',
            task_definition=task_definition_1,
            assign_public_ip=False,
            security_group=fargateSG,
            vpc_subnets=ec2.SubnetSelection(subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE).subnets),
            cluster=fargate_cluster,
            desired_count=2
        )
        # service1_fargateservice.attach_to_application_target_group(service_1_tg)


        # Microservice 2
        service2_ecr_repo = ecr.Repository.from_repository_name(self, 'Service2Repo', vars.ecr_repos[1])
        task_definition_2 = ecs.FargateTaskDefinition(self, 'Service2TaskDefinition',
            cpu=1024,
            memory_limit_mib=2048
        )
        service2_container = task_definition_2.add_container('Service2Container',
            image=ecs.ContainerImage.from_ecr_repository(service2_ecr_repo),
            environment={"region": vars.region}
        )
        service2_container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                host_port=80
            )
        )

        service2_fargateservice = ecs.FargateService(self, 'Service2FargateService',
            task_definition=task_definition_2,
            assign_public_ip=False,
            security_group=fargateSG,
            vpc_subnets=ec2.SubnetSelection(subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE).subnets),
            cluster=fargate_cluster,
            desired_count=2
        )



        # ALB
        # Create ALB
        alb = elb.ApplicationLoadBalancer(self, 'webALB-public',
            vpc=vpc,
            load_balancer_name='webALB-public',
            security_group=webSG,
            internet_facing=True
        )

        # Add listen to ALB
        # alblistener = elb.ApplicationListener(self, 'webALB-Listener',
        #     load_balancer=alb,
        #     default_target_groups=[service_1_tg],
        #     port=80
        # )

        #Add target group 1 to ALB
        service_1_tg = elb.ApplicationTargetGroup(self, 'Service1TargetGroup',
            port=80,
            vpc=vpc,
            target_type=elb.TargetType.IP,
            target_group_name='Service1TG',
            targets=[service1_fargateservice.load_balancer_target(
                container_name='Service1Container',
                container_port=80
            )]
        )

        # Add target group 2 to ALB
        service_2_tg = elb.ApplicationTargetGroup(self, 'Service2TargetGroup',
            port=80,
            vpc=vpc,
            target_type=elb.TargetType.IP,
            target_group_name='Service2TG',
            targets=[service1_fargateservice.load_balancer_target(
                container_name='Service1Container',
                container_port=80
            )]
        )

        
        alblistener = alb.add_listener('webALB-Listener', 
            port=80, 
            open=True,
            default_target_groups=[service_1_tg]
        )

        alblistenerrule_1 = elb.ApplicationListenerRule(self, 'webALB-ListenerRule1',
            path_pattern=vars.paths[0],
            priority=1,
            listener=alblistener,
            target_groups=[service_1_tg]
        )

        alblistenerrule_2 = elb.ApplicationListenerRule(self, 'webALB-ListenerRule2',
            path_pattern=vars.paths[1],
            priority=2,
            listener=alblistener,
            target_groups=[service_2_tg]
        )

        # alblistener.add_targets('Service1Target',
        #     port=80,
        #     targets=service1_fargateservice.load_balancer_target(
        #         container_name='Service1Container',
        #         container_port=80
        #     ),
        #     path_pattern='/service1'
        # )

        # alblistener.add_targets('Service2Target',
        #     port=80,
        #     targets=service2_fargateservice.load_balancer_target(
        #         container_name='Service2Container',
        #         container_port=80
        #     ),
        #     path_pattern='/service2'
        # )


