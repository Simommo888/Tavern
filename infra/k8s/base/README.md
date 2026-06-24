# Tavern Kubernetes Base

第一阶段仅保留 Kubernetes 部署边界说明，正式 manifests 在 Docker Compose 与 API/Web/Worker 稳定后补齐。

计划资源：

- `api-deployment.yaml` / `api-service.yaml`
- `worker-deployment.yaml`
- `web-deployment.yaml` / `web-service.yaml`
- `configmap.yaml`
- `secret.example.yaml`
- `ingress.yaml`
- `hpa.yaml`
- `pdb.yaml`
- `networkpolicy.yaml`

生产建议：PostgreSQL、Redis、RabbitMQ、MinIO、Milvus 优先使用托管服务或 Operator；应用层只保留 API、Worker、Web 三类 Deployment。
