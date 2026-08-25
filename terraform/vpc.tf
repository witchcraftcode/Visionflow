resource "aws_vpc" "visionflow" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "visionflow-vpc"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.visionflow.id

  tags = {
    Name = "visionflow-igw"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.visionflow.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-southeast-2a"
  map_public_ip_on_launch = true

  tags = {
    Name = "visionflow-public-a"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.visionflow.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "ap-southeast-2b"
  map_public_ip_on_launch = true

  tags = {
    Name = "visionflow-public-b"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.visionflow.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "visionflow-public-rt"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}