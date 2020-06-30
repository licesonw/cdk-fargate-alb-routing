#!/usr/bin/env python3

from aws_cdk import core

from fargate_cdk.fargate_cdk_stack import FargateCdkStack


app = core.App()
FargateCdkStack(app, "fargate-cdk")

app.synth()
