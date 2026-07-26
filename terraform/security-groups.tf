resource "aws_security_group" "alb" {
  name        = "${local.name}-alb-sg"
  description = "Allows public HTTP access to the Cloud Black Friday Demo ALB"
  vpc_id      = data.aws_vpc.selected.id

  ingress {
    description = "Public HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name}-alb-sg"
    Role = "load-balancer"
  })
}

resource "aws_security_group" "app" {
  name        = "${local.name}-app-sg"
  description = "Allows application traffic only from the ALB"
  vpc_id      = data.aws_vpc.selected.id

  ingress {
    description     = "Application traffic from ALB"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name}-app-sg"
    Role = "application"
  })
}

resource "aws_security_group" "redis" {
  name        = "${local.name}-redis-sg"
  description = "Allows Redis access only from application instances"
  vpc_id      = data.aws_vpc.selected.id

  ingress {
    description     = "Redis access from application instances"
    from_port       = var.redis_port
    to_port         = var.redis_port
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    description = "Outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name}-redis-sg"
    Role = "redis"
  })
}
