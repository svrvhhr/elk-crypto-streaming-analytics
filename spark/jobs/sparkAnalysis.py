#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, sum as fsum, count, stddev,
    to_timestamp, date_trunc, max as fmax, min as fmin
)

# =========================
# Paramètres
# =========================
ES_INDEX = "cryptodata"
OUT = "/opt/spark/results"

# =========================
# Spark Session
# =========================
spark = SparkSession.builder \
    .appName("CryptoAnalysis-Simple") \
    .config("spark.es.nodes", "elasticsearch") \
    .config("spark.es.port", "9200") \
    .config("spark.es.nodes.wan.only", "true") \
    .getOrCreate()

# =========================
# Lire depuis Elasticsearch
# =========================
df_raw = spark.read.format("org.elasticsearch.spark.sql").load(ES_INDEX)

# =========================
# Nettoyage minimal + typage date
# =========================
df = df_raw.select(
    "coin_id", "name", "symbol",
    "current_price", "market_cap", "total_volume",
    "ingested_at", "last_updated"
).withColumn("ingested_ts", to_timestamp(col("ingested_at"))) \
 .filter(col("coin_id").isNotNull()) \
 .filter(col("current_price").isNotNull()) \
 .filter(col("market_cap").isNotNull())

df.limit(1).count()

# ============================================================
# A) ANALYSES DATAFRAME (Spark SQL-like)
# ============================================================

# A1) Résumé global du marché
market_summary = df.agg(
    count("*").alias("n_docs"),
    avg("current_price").alias("avg_price_global"),
    fmax("current_price").alias("max_price_global"),
    fmin("current_price").alias("min_price_global"),
    fsum("market_cap").alias("sum_market_cap_global"),
    fsum("total_volume").alias("sum_volume_global"),
)
market_summary.write.mode("overwrite").json(f"{OUT}/market_summary_df")

# A2) Statistiques par coin
coin_stats = df.groupBy("coin_id", "name", "symbol").agg(
    avg("current_price").alias("avg_price"),
    fmax("current_price").alias("max_price"),
    fmin("current_price").alias("min_price"),
    stddev("current_price").alias("price_volatility_stddev"),
    avg("market_cap").alias("avg_market_cap"),
    avg("total_volume").alias("avg_volume"),
    count("*").alias("n_records"),
)
coin_stats.write.mode("overwrite").json(f"{OUT}/coin_stats_df")

# A3) Top 10 par market cap
top10_marketcap = coin_stats.orderBy(col("avg_market_cap").desc()).limit(10)
top10_marketcap.write.mode("overwrite").json(f"{OUT}/top10_marketcap_df")

# A4) Top 10 par volume échangé (remplace gainers/losers)
top10_volume = coin_stats.orderBy(col("avg_volume").desc()).limit(10)
top10_volume.write.mode("overwrite").json(f"{OUT}/top10_volume_df")

# A5) Top 10 par volatilité (stddev prix)
top10_volatility = coin_stats.orderBy(col("price_volatility_stddev").desc()).limit(10)
top10_volatility.write.mode("overwrite").json(f"{OUT}/top10_volatility_df")

# A6) Série temporelle par heure
ts_hourly = df.filter(col("ingested_ts").isNotNull()) \
    .withColumn("hour", date_trunc("hour", col("ingested_ts"))) \
    .groupBy("hour") \
    .agg(
        avg("current_price").alias("avg_price_all"),
        fsum("total_volume").alias("sum_volume_all"),
        fsum("market_cap").alias("sum_market_cap_all"),
        count("*").alias("n_records")
    ).orderBy("hour")

ts_hourly.write.mode("overwrite").json(f"{OUT}/time_series_hourly_df")

# ============================================================
# B) RDD / MAPREDUCE
# Prix moyen par coin (map -> reduceByKey -> moyenne)
# ============================================================

rdd = df.select("coin_id", "current_price") \
    .filter(col("coin_id").isNotNull() & col("current_price").isNotNull()) \
    .rdd

# MAP: (coin_id, (sum_price, count))
mapped = rdd.map(lambda r: (r["coin_id"], (float(r["current_price"]), 1)))

# REDUCE: additionner les tuples
reduced = mapped.reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1]))

# FINAL: moyenne = sum / count
avg_price_mr = reduced.mapValues(lambda x: x[0] / x[1])

avg_price_mr.toDF(["coin_id", "avg_price_mr"]) \
    .write.mode("overwrite").json(f"{OUT}/avg_price_mr")

# =========================
# Fin
# =========================
spark.stop()
print("✅ Spark terminé. Résultats dans :", OUT)