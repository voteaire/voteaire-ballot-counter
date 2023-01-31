# networking

resource "aws_vpc" "testnet_voteaire_vpc" {
  assign_generated_ipv6_cidr_block = "false"
  cidr_block                       = "10.110.0.0/18"
  enable_dns_hostnames             = "true"

  tags = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc"
  }

  tags_all = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc"
  }
}

resource "aws_internet_gateway" "testnet_voteaire_gw" {
  vpc_id = aws_vpc.testnet_voteaire_vpc.id

  tags = {
    Name = "testnet_voteaire"
  }
}
# security groups

resource "aws_security_group" "worker_sg" {
  description = "Security group for workers"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  name   = "worker-sg"
  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}
# sg-07e072beadb647d73
resource "aws_security_group" "voteaire_api_ecs_sg" {
  description = "Security group for voteaire api ecs service"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "80"
    protocol    = "tcp"
    self        = "false"
    to_port     = "80"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "8080"
    protocol    = "tcp"
    self        = "false"
    to_port     = "8080"
  }

  name   = "voteaire-api-ecs-sg"
  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}


resource "aws_security_group" "lb_sg" {
  description = "sec group for api load balancer"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "443"
    protocol    = "tcp"
    self        = "false"
    to_port     = "443"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "80"
    protocol    = "tcp"
    self        = "false"
    to_port     = "80"
  }

  name   = "voteaire-api-lb-sg"
  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}

# subnets
# subnet-00c663233a48d1bcc
resource "aws_subnet" "private-d" {
  assign_ipv6_address_on_creation                = "false"
  cidr_block                                     = "10.110.5.0/24"
  enable_dns64                                   = "false"
  enable_resource_name_dns_a_record_on_launch    = "false"
  enable_resource_name_dns_aaaa_record_on_launch = "false"
  ipv6_native                                    = "false"
  map_public_ip_on_launch                        = "false"
  private_dns_hostname_type_on_launch            = "ip-name"
  availability_zone                              = "ca-central-1d"

  tags = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-private-ca-central-1d"
  }

  tags_all = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-private-ca-central-1d"
  }

  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}
# subnet-0398292cd5b84838d
resource "aws_subnet" "public-d" {
  assign_ipv6_address_on_creation                = "false"
  cidr_block                                     = "10.110.2.0/24"
  enable_dns64                                   = "false"
  enable_resource_name_dns_a_record_on_launch    = "false"
  enable_resource_name_dns_aaaa_record_on_launch = "false"
  ipv6_native                                    = "false"
  map_public_ip_on_launch                        = "true"
  private_dns_hostname_type_on_launch            = "ip-name"
  availability_zone                              = "ca-central-1d"

  tags = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-public-ca-central-1d"
  }

  tags_all = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-public-ca-central-1d"
  }

  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}
# subnet-0a079928f85d76281
resource "aws_subnet" "public-a" {
  assign_ipv6_address_on_creation                = "false"
  cidr_block                                     = "10.110.0.0/24"
  enable_dns64                                   = "false"
  enable_resource_name_dns_a_record_on_launch    = "false"
  enable_resource_name_dns_aaaa_record_on_launch = "false"
  ipv6_native                                    = "false"
  map_public_ip_on_launch                        = "true"
  private_dns_hostname_type_on_launch            = "ip-name"
  availability_zone                              = "ca-central-1a"

  tags = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-public-ca-central-1a"
  }

  tags_all = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-public-ca-central-1a"
  }

  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}
# subnet-0bd72c79ab169ae48
resource "aws_subnet" "public-b" {
  assign_ipv6_address_on_creation                = "false"
  cidr_block                                     = "10.110.1.0/24"
  enable_dns64                                   = "false"
  enable_resource_name_dns_a_record_on_launch    = "false"
  enable_resource_name_dns_aaaa_record_on_launch = "false"
  ipv6_native                                    = "false"
  map_public_ip_on_launch                        = "true"
  private_dns_hostname_type_on_launch            = "ip-name"
  availability_zone                              = "ca-central-1b"

  tags = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-public-ca-central-1b"
  }

  tags_all = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-public-ca-central-1b"
  }

  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}
#subnet-0c590e5e75a77d588
resource "aws_subnet" "private-a" {
  assign_ipv6_address_on_creation                = "false"
  cidr_block                                     = "10.110.3.0/24"
  enable_dns64                                   = "false"
  enable_resource_name_dns_a_record_on_launch    = "false"
  enable_resource_name_dns_aaaa_record_on_launch = "false"
  ipv6_native                                    = "false"
  map_public_ip_on_launch                        = "false"
  private_dns_hostname_type_on_launch            = "ip-name"
  availability_zone                              = "ca-central-1a"

  tags = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-private-ca-central-1a"
  }

  tags_all = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-private-ca-central-1a"
  }

  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}
#subnet-0e409e0801a1e4207
resource "aws_subnet" "private-b" {
  assign_ipv6_address_on_creation                = "false"
  cidr_block                                     = "10.110.4.0/24"
  enable_dns64                                   = "false"
  enable_resource_name_dns_a_record_on_launch    = "false"
  enable_resource_name_dns_aaaa_record_on_launch = "false"
  ipv6_native                                    = "false"
  map_public_ip_on_launch                        = "false"
  private_dns_hostname_type_on_launch            = "ip-name"
  availability_zone                              = "ca-central-1b"

  tags = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-private-ca-central-1b"
  }

  tags_all = {
    Environment = "production"
    Name        = "testnet-voteaire-vpc-private-ca-central-1b"
  }

  vpc_id = aws_vpc.testnet_voteaire_vpc.id
}


# load balancer

resource "aws_lb" "testnet_voteaire_lb" {
  desync_mitigation_mode     = "defensive"
  drop_invalid_header_fields = "false"
  enable_deletion_protection = "false"
  enable_http2               = "true"
  enable_waf_fail_open       = "false"
  idle_timeout               = "60"
  internal                   = "false"
  ip_address_type            = "ipv4"
  load_balancer_type         = "application"
  name                       = "testnet-voteaire-lb"
  security_groups            = [aws_security_group.lb_sg.id]

  subnets = [aws_subnet.public-a.id, aws_subnet.public-b.id]
}

resource "aws_lb_listener" "voteaire_lb_listener" {
  certificate_arn = "arn:aws:acm:ca-central-1:044223142297:certificate/90b75eed-405b-4287-a8e6-f4c875a40aa1"

  default_action {
    target_group_arn = aws_lb_target_group.testnet_voteaire_api_tg_1.arn
    type             = "forward"
  }

  load_balancer_arn = aws_lb.testnet_voteaire_lb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
}

resource "aws_lb_listener" "voteaire_lb_listener_container" {
  default_action {
    target_group_arn = aws_lb_target_group.testnet_voteaire_api_tg_2.arn
    type             = "forward"
  }

  load_balancer_arn = aws_lb.testnet_voteaire_lb.arn
  port              = "8080"
  protocol          = "HTTP"
}

resource "aws_lb_target_group" "testnet_voteaire_api_tg_1" {
  deregistration_delay = "300"

  health_check {
    enabled             = "true"
    healthy_threshold   = "5"
    interval            = "30"
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = "5"
    unhealthy_threshold = "2"
  }

  load_balancing_algorithm_type = "round_robin"
  name                          = "testnet-voteaire-api-tg-1"
  port                          = "80"
  protocol                      = "HTTP"
  protocol_version              = "HTTP1"
  slow_start                    = "0"

  stickiness {
    cookie_duration = "86400"
    enabled         = "false"
    type            = "lb_cookie"
  }

  target_type = "ip"
  vpc_id      = aws_vpc.testnet_voteaire_vpc.id
}

resource "aws_lb_target_group" "testnet_voteaire_api_tg_2" {
  deregistration_delay = "300"

  health_check {
    enabled             = "true"
    healthy_threshold   = "5"
    interval            = "30"
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = "5"
    unhealthy_threshold = "2"
  }

  load_balancing_algorithm_type = "round_robin"
  name                          = "testnet-voteaire-api-tg-2"
  port                          = "80"
  protocol                      = "HTTP"
  protocol_version              = "HTTP1"
  slow_start                    = "0"

  stickiness {
    cookie_duration = "86400"
    enabled         = "false"
    type            = "lb_cookie"
  }

  target_type = "ip"
  vpc_id      = aws_vpc.testnet_voteaire_vpc.id

}
