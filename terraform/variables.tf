variable "aws_region" {
  default = "ap-southeast-2"
}

variable "cluster_name" {
  default = "visionflow-eks"
}

variable "node_instance_type" {
  default = "t3.small"
}

variable "desired_nodes" {
  default = 2
}