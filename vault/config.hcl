storage "raft" {
  path    = "/vault/data"
  node_id = "node1"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1 # Enable TLS in prod
}

api_addr = "http://vault:8200"
cluster_addr = "http://vault:8201"
ui = true