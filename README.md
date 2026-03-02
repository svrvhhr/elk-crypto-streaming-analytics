# 🪙 ELK Crypto Streaming Analytics

> Real-Time Cryptocurrency Data Pipeline with Kafka, Spark & Elastic Stack

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Spark](https://img.shields.io/badge/Apache%20Spark-3.x-orange?logo=apachespark)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-7.x-005571?logo=elasticsearch)
![Kafka](https://img.shields.io/badge/Apache%20Kafka-latest-black?logo=apachekafka)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

A real-time Big Data pipeline for collecting, processing, analyzing, and visualizing cryptocurrency market data. This project demonstrates a modern streaming analytics architecture using **Kafka**, **Logstash**, **Elasticsearch**, **Kibana**, and **Apache Spark**.

> ⚠️ **Resource requirements:** This stack runs Kafka + Spark + ELK simultaneously.
> Minimum recommended: **8 GB RAM** and **4 CPU cores**.

---

## 🎯 Features

### 🔄 Real-Time Data Collection
- Automatic polling of the CoinGecko API
- Cryptocurrency market data: price, market cap, volume, change %
- JSON normalization before streaming
- Publishing structured messages to Kafka topic `cryptodata`
- Configurable polling interval

### ⚡ Stream Processing (ELK Stack)
- Kafka → Logstash ingestion
- Data transformation & enrichment
- Custom Elasticsearch index mapping
- Edge N-gram analyzer for autocomplete search
- Optimized index for aggregations & analytics

### 🧠 Distributed Analytics with Spark
- Elasticsearch as data source
- DataFrame-based aggregations:
  - Market summary
  - Top 10 coins by market cap
  - Top 10 by volume
  - Volatility ranking (stddev)
  - Time-series analysis (hourly)
- RDD MapReduce example: average price per coin (map → reduceByKey)
- Results exported as JSON
- Optional write-back to Elasticsearch

### 📊 Visualization with Kibana
- Discover exploration
- Interactive dashboards
- Market overview dashboard
- Performance & volatility dashboard
- Time-based filtering
- Autocomplete search via `edge_ngram` analyzer

---

## 🏗️ Architecture

```
CoinGecko API
      │
      ▼
Producer (Python)
      │
      ▼
Kafka (Topic: cryptodata)
      │
      ▼
Logstash
      │
      ▼
Elasticsearch (Index: cryptodata)
      │
┌─────┴──────────┐
▼                ▼
Kibana      Apache Spark
                 │
                 ▼
          JSON Results / Analytics
          (spark_results/)
```

---

## 📁 Project Structure

```
elk-crypto-streaming-analytics/
│
├── docker-compose.yml
├── .env.example
├── README.md
│
├── producer/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── producer.py
│
├── elk/
│   ├── elasticsearch/
│   │   └── cryptodata.json        # Index mapping + edge_ngram analyzer
│   ├── logstash/
│   │   ├── pipelines.yml
│   │   └── cryptodata.conf        # Kafka → Elasticsearch pipeline
│   └── kibana/
│
├── spark/
│   └── jobs/
│       └── sparkAnalysis.py       # Spark analytics job
│
└── spark_results/                 # JSON outputs from Spark
```

---

## ⚙️ Tech Stack

| Component | Version |
|---|---|
| Python | 3.10+ |
| Apache Kafka | latest |
| Logstash | 7.x |
| Elasticsearch | 7.x |
| Kibana | 7.x |
| Apache Spark | 3.x |
| Docker Compose | 2.x+ |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/svrvhhr/elk-crypto-streaming-analytic.git
cd elk-crypto-streaming-analytic
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit the `.env` file with your values:

```env
# CoinGecko API key (optional for public endpoints)
COINGECKO_API_KEY=        # Leave empty if using the free public API

# Polling interval in seconds
POLL_SECONDS=60

# Kafka
KAFKA_TOPIC=cryptodata
```

### 3. Start All Services

```bash
docker compose up -d --build
```

Check that all services are running:

```bash
docker compose ps
```

---

## 🌐 Access Interfaces

| Service | URL |
|---|---|
| Kibana | http://localhost:5601 |
| Elasticsearch | http://localhost:9200 |
| Spark Master UI | http://localhost:8080 |
| Spark Worker UI | http://localhost:8081 |

---

## 🔎 Elasticsearch

Verify the cluster is healthy:

```bash
curl http://localhost:9200
```

Check indexed documents:

```bash
curl http://localhost:9200/cryptodata/_count
```

Inspect a sample document:

```bash
curl http://localhost:9200/cryptodata/_search?size=1&pretty
```

---

## 🧠 Spark Analytics

Spark reads directly from Elasticsearch using the connector:

```
org.elasticsearch:elasticsearch-spark-30_2.12
```

### Manual Execution

```bash
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.elasticsearch:elasticsearch-spark-30_2.12:7.16.2 \
  /opt/spark/jobs/sparkAnalysis.py
```

### What the Spark Job Computes

- ✔ Global market summary
- ✔ Statistics per coin
- ✔ Top 10 by market cap
- ✔ Top 10 by volume
- ✔ Top 10 most volatile assets (stddev)
- ✔ Hourly time-series analysis
- ✔ RDD MapReduce — average price per coin

Results are exported to `spark_results/` as JSON files.

---

## 📊 Kibana Dashboard Setup

1. Open Kibana → **Stack Management** → **Data Views**
2. Create a Data View:
   - Pattern: `cryptodata*`
   - Time field: `@timestamp` or `ingested_at`

### Recommended Dashboards

**📌 Market Overview**
- Total market cap (sum)
- Total volume (sum)
- Top 10 coins by market cap
- Price & volume table

**📌 Performance & Volatility**
- Stddev(price) per coin
- Top volatile assets
- Price distribution
- Time-series price evolution

---

## 🧪 Testing & Validation

Check container status:

```bash
docker compose ps
docker compose logs -f producer
```

List Kafka topics:

```bash
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

Check Elasticsearch indices:

```bash
curl http://localhost:9200/_cat/indices?v
```

Check Spark version:

```bash
docker exec spark-master /opt/spark/bin/spark-submit --version
```

---

## 🧹 Cleanup

```bash
# Stop all services
docker compose down

# Stop and remove volumes (full reset)
docker compose down -v
```

---
