# Some variables to configure

ecr_repos = [
    'service1-nginx',
    'service2-nginx'
]

paths = [
    '/service1/*',
    '/service2/*'
]

num_tasks = [
    2,
    2
]

cidr = '10.0.0.0/16'
region = 'eu-central-1'