🚦 Real-Time Spatiotemporal Traffic Intelligence System
📌 Overview

This project implements a real-time traffic intelligence platform that transforms streaming GPS data into actionable insights about traffic behavior.

Instead of treating location data in isolation, the system models traffic as a spatiotemporal phenomenon, integrating space, time, and traffic attributes to detect congestion, identify hotspots, analyze movement patterns, and track how traffic evolves over time.

🧠 Approach

Traffic patterns are inherently dependent on spatial proximity, temporal continuity, and behavioral attributes.
To capture this, the system is built around:

Spatiotemporal similarity modeling
Density-based clustering
Statistical validation
Temporal pattern analysis
Change detection

Each stage progressively refines raw data into meaningful traffic intelligence.

<img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/971905a2-9a3b-4b6d-820a-492ec94be54a" />

🔑 Core Functionality
Spatiotemporal Similarity
Composite distance combining location, time, and traffic features
Traffic Clustering
ST-DBSCAN based grouping of data into congestion zones
Hotspot Detection
Statistical validation to identify significant congestion regions
Trajectory & Anomaly Analysis
Detection of movement patterns and irregular behaviors
Traffic Regime Modeling
Classification of traffic states such as free-flow and congestion
Drift Detection
Identification of changes in traffic patterns across time
Incremental Updates
Efficient real-time updates without full recomputation
Visualization Dashboard
Live monitoring of clusters, hotspots, and traffic conditions
🖥️ System Interaction

The system is designed for interactive execution and monitoring:

A FastAPI backend serves as the control layer
A frontend interface is used to:
Trigger Kafka streaming
Start the processing pipeline
Monitor outputs in real time

This ensures the entire workflow can be controlled without manual terminal operations.

▶️ Running the System

Start the application using two terminals:

# Backend (FastAPI)
uvicorn api:app --host 127.0.0.1 --port 8000 --reload

# Frontend (UI)
npm run dev

Once running:

Data streaming is initiated from the frontend
The pipeline executes automatically
Results are updated live on the dashboard
📊 Data Representation

Each data point is modeled as a spatiotemporal traffic observation:

Latitude, Longitude
Timestamp
Speed
Density
Flow

Synthetic data is used to simulate realistic traffic scenarios including congestion peaks, anomalies, and evolving traffic patterns.

📚 Research Alignment

This system is grounded in spatiotemporal data mining principles, where each component aligns with a theoretical concept:

Spatiotemporal similarity → composite distance
Density-based clustering → ST-DBSCAN
Statistical hotspot detection → scan statistics
Outlier detection → trajectory anomalies
Prediction → traffic regime modeling
Change detection → drift analysis









