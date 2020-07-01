
# Path-based microservices routing with ALB and AWS Fargate

This CDK app allows you to easily define ECR repositories with Docker images and deploy them with AWS Fargate behind an Application Load Balancer with path-based routing.

## Getting started

First, set up the configuration file `fargate_config.json` to pass the parameters of your microservices application. The structure of the file is as follows:
```
{
    "region": "eu-central-1",
    "cidr": "10.0.0.0/16",
    "containers": [
        {
            "service_name": "service1",
            "ecr_repo": "service1-nginx",
            "alb_routing_path": "/service1/*",
            "num_tasks": 2
        },
        {
            "service_name": "service2",
            "ecr_repo": "service2-nginx",
            "alb_routing_path": "/service2/*",
            "num_tasks": 3
        }
    ]
}
```

```
# Deploy the stack
cdk deploy
```

