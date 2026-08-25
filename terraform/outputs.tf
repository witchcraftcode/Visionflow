output "vpc_id" {
  value = aws_vpc.visionflow.id
}

output "public_subnet_a" {
  value = aws_subnet.public_a.id
}

output "public_subnet_b" {
  value = aws_subnet.public_b.id
}

output "cluster_name" {
  value = aws_eks_cluster.visionflow.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.visionflow.endpoint
}