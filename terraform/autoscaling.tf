resource "aws_autoscaling_group" "app" {
  name                      = "${local.name}-asg"
  min_size                  = var.asg_min_size
  desired_capacity          = var.asg_desired_capacity
  max_size                  = var.asg_max_size
  default_cooldown          = 300
  default_instance_warmup   = 45
  health_check_type         = "ELB"
  health_check_grace_period = 60
  vpc_zone_identifier       = var.subnet_ids
  target_group_arns         = [aws_lb_target_group.app.arn]
  termination_policies      = ["Default"]

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }

  instance_refresh {
    strategy = "Rolling"

    preferences {
      min_healthy_percentage = 50
      instance_warmup        = 45
    }

  }

  dynamic "tag" {
    for_each = merge(local.common_tags, {
      Name      = "${local.name}-app-asg"
      Role      = "application"
      ManagedBy = "auto-scaling"
    })

    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }

  lifecycle {
    ignore_changes = [desired_capacity]
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_autoscaling_policy" "cpu_target_tracking" {
  name                   = "${local.name}-cpu-policy"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }

    target_value     = var.cpu_target_value
    disable_scale_in = false
  }
}
