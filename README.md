
# Path-based microservices routing with ALB and AWS Fargate

This CDK app allows you to easily deploy Docker images (either in ECR or Docker Hub) with AWS Fargate behind an Application Load Balancer with path-based routing. Additionally, the app will set up a private DNS namespace with Route 53 and AWS CloudMap to enable service discovery and allow for standardized communication between services.

## Architecture

![architecture](images/cdk-fargate-architecture.png)

## Getting started

First, set up the configuration file `fargate_config.json` to pass the parameters of your microservices application. You can define the following parameters:

* `"cidr"`: The cidr block for the VPC that is created for the cluster
* `"service_discovery_namespace"`: The private DNS namespace that defines under which private domain your services / individual containers are reachable.
* `"services"`: An array of service objects, each service defines one of your dockerized microservices.
* `"service_name"`: The name of the microservice
* `"repo"`: The name of the repository (DockerHub, ECR or others) where the Docker images resides. The app will always take the `:latest` tag, unless specified otherwise.
* `"alb_routing_path"`: The URL path that defines to which service the load balancer will route the request
* `"num_tasks"`: The number of desired tasks per service
* `"service_discovery_service_name"`: Under which subdomain your service will be registered with the Route 53 namespace.


The structure of the config file is as follows:
```json
{
    "region": "eu-central-1",
    "cidr": "10.0.0.0/16",
    "service_discovery_namespace": "cdkapps.local",
    "services": [
        {
            "service_name": "service1",
            "repo": "service1-nginx",
            "alb_routing_path": "/service1/*",
            "num_tasks": 2,
            "service_discovery_service_name": "service1"
        },
        {
            "service_name": "service2",
            "repo": "service2-nginx",
            "alb_routing_path": "/service2/*",
            "num_tasks": 3,
            "service_discovery_service_name": "service2"
        }
    ]
}
```

Finally, deploy the stack with the CDK command.
```bash
# Deploy the stack
cdk deploy
```

## Set up some sample Docker images
Make sure that your container serves the content in the corresponding path. To try out this infrastructure quickly, you can set up a several nginx images that serve a static HTML page. To serve a single static file from all URL paths, copy a different `index.html` to `/usr/share/nginx/html` for each Docker image and configure nginx as:
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    location / {
        try_files /index.html /index.html;
    }
}
```

The simplest Dockerfile you can use would look something like this:
```Dockerfile
FROM nginx
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/
COPY . /usr/share/nginx/html
```

Then, push your images to ECR following [this](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html) tutorial.

## Further reading
* https://docs.aws.amazon.com/elasticloadbalancing/latest/application/tutorial-load-balancer-routing.html
* ...

