locals {
  config = jsondecode(file("${path.module}/config.json"))
}