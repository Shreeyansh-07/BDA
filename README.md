# 🎬 Scalable Movie Recommendation System (Big Data Pipeline)

An end-to-end **movie recommendation system** built with **Apache Spark (MLlib), Hadoop HDFS, and Streamlit**, delivering **real-time, personalized recommendations** on large-scale data.

---

## 🚀 Overview

This project implements a **production-style recommendation pipeline** that combines:

* ⚡ **Distributed processing** with Apache Spark
* 🗄️ **Scalable storage** with Hadoop HDFS
* 🧠 **Collaborative filtering (ALS)** for recommendations
* 🌐 **Interactive UI** with Streamlit
* 🎞️ **Content enrichment** via TMDb API (posters, metadata)

Unlike typical academic setups, this system covers the **full stack**: data ingestion → model training → serving → user interface.

---

## 🧠 Problem

Modern recommender systems must:

* Scale to millions of interactions
* Provide low-latency recommendations
* Deliver a usable, interactive experience

This project addresses all three with a **distributed ML pipeline + real-time UI**.

---

## 🏗️ Architecture

### 🔹 Data Layer

* **Dataset:** MovieLens 32M
* **Storage:** Hadoop HDFS
* **Processing:** PySpark (distributed)

### 🔹 Modeling

* **Algorithm:** ALS (Alternating Least Squares)
* **Type:** Collaborative Filtering (implicit feedback)
* **Library:** Spark MLlib

### 🔹 Serving

* Top-N recommendations per user
* Spark-based generation (`recommendForAllUsers`)
* Low-latency responses

### 🔹 Frontend

* Built with **Streamlit**
* Supports:

  * 👤 Logged-in users (personalized recs)
  * 👥 Guest mode (filters: genre, year)

### 🔹 API Enrichment

* **TMDb API** for:

  * Posters
  * Movie details
  * Visual experience

---

## 📊 Performance

| Metric                   | Result      |
| ------------------------ | ----------- |
| RMSE (Spark ALS)         | **~0.81**   |
| RMSE (baseline notebook) | ~3.68       |
| Training Time            | < 8 minutes |
| Recommendation Latency   | < 2 seconds |

---

## ✨ Key Features

* Distributed training with Spark MLlib
* Scalable storage using HDFS
* Real-time recommendation serving
* Interactive Streamlit UI
* External API integration (TMDb)
* Modular, reproducible pipeline

---

## 📁 Project Structure

```text
BigData_Phase3/
│
├── Notebook.ipynb          # Baseline / exploration
├── SparkNotebook.ipynb     # Distributed pipeline (Spark)
├── app/                    # (optional) Streamlit app
├── models/                 # Saved ALS model (optional)
├── data/                   # (external / HDFS)
├── requirements.txt
└── README.md
```

---

## ▶️ How to Run

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Run Spark pipeline

```bash
spark-submit your_training_script.py
```

### 3) Launch Streamlit app

```bash
streamlit run app/streamlit_app.py
```

---

## 📥 Dataset

Large datasets are not included due to size limits.

* MovieLens: https://grouplens.org/datasets/movielens/

---

## 🧪 Evaluation

* **RMSE** → prediction accuracy
* **Precision@K** → recommendation relevance
* **Latency** → real-time usability

---

## 🧠 Key Contributions

* End-to-end **big data ML pipeline**
* Practical **real-time recommendation system**
* Integration of **Spark + HDFS + Streamlit**
* Balance between **scalability, accuracy, and usability**

---

## ⚠️ Limitations

* Cold-start problem for new users/items
* Full performance requires distributed setup

---

## 🚀 Future Work

* Hybrid models (collaborative + content-based)
* Kubernetes / microservices deployment
* Mobile-friendly UI
* Deep learning recommenders

---

## 🧰 Tech Stack

* Apache Spark (MLlib)
* Hadoop HDFS
* Python
* Streamlit
* TMDb API
* Docker (optional)

---

## 👤 Author

**Fadwa Hany**

---

## ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub!
