resource "aws_instance" "redis" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.redis_subnet_id
  vpc_security_group_ids      = [aws_security_group.redis.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  associate_public_ip_address = true
  ebs_optimized               = true
  monitoring                  = false
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
    instance_metadata_tags      = "disabled"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    iops                  = 3000
    throughput            = 125
    encrypted             = false
    delete_on_termination = true
  }

  user_data = templatefile("${path.module}/user-data-redis.sh.tftpl", {
    redis_port = var.redis_port
  })

  tags = merge(local.common_tags, {
    Name      = "${local.name}-redis"
    Role      = "redis"
    ManagedBy = "terraform"
  })

  depends_on = [aws_iam_role_policy_attachment.ssm]
}
