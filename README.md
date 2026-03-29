# Spatio-Temporal Mobility Mining Platform

## Overview

This project implements a real-time spatio-temporal data mining system for intelligent mobility analysis. It processes GPS-based traffic data streams to identify congestion patterns, detect anomalies, and analyze traffic behavior over time.

The system integrates clustering, streaming, trajectory mining, and time-series analysis into a unified pipeline to simulate real-world urban mobility intelligence.

---

## System Architecture

The system follows a streaming pipeline:

```
CSV Data → Kafka Producer → Kafka Topic → Kafka Consumer
        → Clustering → Hotspot Detection
        → Trajectory Mining → MVTS Analysis → Drift Detection
```

---

## Core Features

* Real-time data streaming using Apache Kafka
* Spatio-temporal clustering using ST-DBSCAN
* Composite distance function (spatial + temporal + traffic features)
* Hotspot detection for congestion zones
* Trajectory mining using DTW (Dynamic Time Warping)
* Traffic regime classification (gridlock, congested, slow, free flow)
* Drift detection for detecting long-term behavioral changes

---

## Project Structure

```
composite_distance.py   # Computes spatial + temporal + traffic similarity
st_clustering.py        # ST-DBSCAN clustering implementation
hotspot_validator.py    # Identifies congestion hotspots

kafka_producer.py       # Streams CSV data into Kafka
kafka_consumer.py       # Consumes data from Kafka

trajectory_miner.py     # Extracts movement patterns and anomalies
mvts_analyzer.py        # Traffic regime analysis using Markov model
drift_detector.py       # Detects long-term pattern shifts

generate_data.py        # Synthetic dataset generator
config.py               # Configuration parameters
shared_types.py         # Common data structures (TrafficPoint, Cluster)

pipeline.py             # Main integration pipeline
docker-compose.yml      # Kafka + Zookeeper setup

tests/                  # Unit tests
cluster_map.html        # Visualization output
```

---

## Kafka Setup

### Step 1: Start Docker

Ensure Docker Desktop is running.

### Step 2: Start Kafka and Zookeeper

```
docker-compose up -d
```

### Step 3: Verify containers

```
docker ps
```

### Step 4: Verify topic

```
docker exec -it <kafka-container-id> kafka-topics --list --bootstrap-server localhost:9092
```

Expected output:

```
traffic_stream
```

---

## How to Run the System

### 1. Start Kafka

```
docker-compose up -d
```

---

### 2. Stream data into Kafka

```
python kafka_producer.py --file data/gps_data.csv --speed 100000
```

---

### 3. Run the pipeline

```
python pipeline.py
```

---

## Optional: Test Kafka Consumer

```
python kafka_consumer.py
```

---

## Run Tests

```
python -m pytest tests/test_streaming.py -v
```

---

## Current Scope (v1)

* Processes batches of ~200 points from a dataset of ~5000 points
* Simulates real-time streaming using Kafka
* Performs clustering and analysis per batch
* Outputs clusters, hotspots, trajectory insights, and traffic regimes

Limitations:

* Finite dataset (not continuous streaming)
* Basic hotspot validation (not statistical)
* Limited evaluation metrics
* No frontend/dashboard integration

---

## Future Improvements (Research-Based Enhancements)

Based on spatio-temporal data mining research, the following improvements are planned:

### 1. Advanced Hotspot Detection

* Replace heuristic hotspot detection with statistical scan methods
* Identify statistically significant congestion regions

---

### 2. Temporal Cluster Evolution

* Track how clusters evolve over time
* Detect emerging, merging, and disappearing hotspots

---

### 3. Improved Drift Detection

* Use statistical change detection methods instead of simple similarity metrics
* Detect concept drift more robustly in streaming data

---

### 4. Evaluation Metrics

* Add clustering validation metrics:

  * Silhouette Score
  * Davies–Bouldin Index
* Measure temporal stability of clusters

---

### 5. Continuous Streaming Data

* Replace finite CSV input with continuous data generation
* Simulate real-world traffic streams

---

### 6. Backend API Layer

* Build APIs to expose:

  * clusters
  * hotspots
  * predictions
* Enable integration with external systems

---

### 7. Frontend Dashboard

* Interactive visualization of clusters and hotspots
* Real-time map-based interface
* Traffic regime monitoring

---

## Conclusion

This project demonstrates a unified approach to spatio-temporal data mining by combining clustering, streaming, pattern mining, and predictive analysis into a single system.

It serves as a foundation for scalable, real-time urban mobility intelligence systems.
