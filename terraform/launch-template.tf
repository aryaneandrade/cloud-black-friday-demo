resource "aws_launch_template" "app" {
  name                   = "${local.name}-lt"
  image_id               = var.ami_id
  instance_type          = var.instance_type
  update_default_version = true

  iam_instance_profile {
    arn = aws_iam_instance_profile.ec2.arn
  }

  vpc_security_group_ids = [aws_security_group.app.id]

  monitoring {
    enabled = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  user_data = base64encode(templatefile("${path.module}/user-data-app.sh.tftpl", {
    aws_region   = var.aws_region
    ecr_registry = split("/", aws_ecr_repository.app.repository_url)[0]
    app_image    = local.app_image
    redis_url    = "redis://${aws_instance.redis.private_ip}:${var.redis_port}/0"
    app_port     = var.app_port
  }))

  tag_specifications {
    resource_type = "instance"

    tags = merge(local.common_tags, {
      Name      = "${local.name}-app-asg"
      Role      = "application"
      ManagedBy = "auto-scaling"
    })
  }

  tag_specifications {
    resource_type = "volume"

    tags = merge(local.common_tags, {
      ManagedBy = "auto-scaling"
    })
  }

  depends_on = [
    aws_iam_role_policy_attachment.ecr_pull,
    aws_instance.redis
  ]
}
