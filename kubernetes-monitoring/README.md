# Kubernetes Monitoring with Arc

Monitor your Kubernetes cluster using Telegraf for metrics collection, Arc for storage, and Grafana for visualization.

## Overview

This example deploys a complete monitoring stack:

- **Telegraf DaemonSet** - Collects metrics from every node via the Kubelet API
- **Arc** - Stores time-series data in Parquet files
- **Grafana** - Visualizes metrics with dashboards and alerts

## Quick Start

1. **Deploy Arc**
   ```bash
   kubectl apply -f arc-deployment.yaml
   ```

2. **Get the Arc token**
   ```bash
   kubectl -n monitoring logs deployment/arc | grep "Initial admin"
   ```

3. **Update the token in telegraf-daemonset.yaml**
   ```yaml
   stringData:
     arc-token: "arc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Your token here
   ```

4. **Deploy Telegraf**
   ```bash
   kubectl apply -f telegraf-rbac.yaml
   kubectl apply -f telegraf-config.yaml
   kubectl apply -f telegraf-daemonset.yaml
   ```

5. **Deploy Grafana**
   ```bash
   kubectl apply -f grafana-deployment.yaml
   ```

6. **Install Arc datasource plugin**
   ```bash
   kubectl -n monitoring exec -it deployment/grafana -- /bin/sh
   wget https://github.com/basekick-labs/grafana-arc-datasource/releases/download/v1.0.0/basekick-arc-datasource-1.0.0.zip
   unzip basekick-arc-datasource-1.0.0.zip -d /var/lib/grafana/plugins/
   exit
   kubectl -n monitoring rollout restart deployment/grafana
   ```

7. **Access Grafana** at `http://<node-ip>:30300` (admin/admin)

## Metrics Collected

| Table | Description |
|-------|-------------|
| `kubernetes_pod_container` | Pod CPU, memory, network metrics |
| `kubernetes_node` | Node-level resource usage |
| `cpu` | Host CPU utilization |
| `mem` | Host memory usage |
| `disk` | Disk space and I/O |
| `net` | Network traffic |

## Example Queries

**CPU Usage by Node:**
```sql
SELECT
  time_bucket(INTERVAL '1 minute', time) as time,
  host,
  AVG(usage_idle) * -1 + 100 AS cpu_usage
FROM kubernetes.cpu
WHERE time > NOW() - INTERVAL '1 hour'
GROUP BY 1, 2
ORDER BY time ASC
```

**Memory by Namespace:**
```sql
SELECT
  time_bucket(INTERVAL '1 minute', time) as time,
  namespace,
  SUM(memory_working_set_bytes) / 1024 / 1024 / 1024 AS memory_gb
FROM kubernetes.kubernetes_pod_container
WHERE time > NOW() - INTERVAL '1 hour'
GROUP BY 1, 2
ORDER BY time ASC
```

**Top 10 Pods by CPU:**
```sql
SELECT
  pod_name,
  namespace,
  AVG(cpu_usage_nanocores) / 1000000 AS cpu_millicores
FROM kubernetes.kubernetes_pod_container
WHERE time > NOW() - INTERVAL '15 minutes'
GROUP BY pod_name, namespace
ORDER BY cpu_millicores DESC
LIMIT 10
```

## Full Tutorial

For a complete step-by-step guide with detailed explanations, dashboard screenshots, and alerting configuration, see the blog post:

**[Monitoring Kubernetes with Telegraf, Arc, and Grafana](https://basekick.net/update/kubernetes-monitoring-telegraf-arc-grafana)**

## Files

| File | Description |
|------|-------------|
| `arc-deployment.yaml` | Arc deployment with PVC storage |
| `telegraf-rbac.yaml` | ServiceAccount, ClusterRole, ClusterRoleBinding |
| `telegraf-config.yaml` | Telegraf configuration with kubernetes input |
| `telegraf-daemonset.yaml` | Telegraf DaemonSet + secrets |
| `grafana-deployment.yaml` | Grafana deployment with PVC |

## Requirements

- Kubernetes 1.19+
- kubectl configured
- 10Gi storage for Arc
- 5Gi storage for Grafana

## Resources

- [Arc Documentation](https://docs.basekick.net/arc)
- [Grafana Arc Datasource](https://github.com/basekick-labs/grafana-arc-datasource)
- [Telegraf Kubernetes Plugin](https://docs.influxdata.com/telegraf/latest/plugins/#input-kubernetes)
