FROM apache/spark:3.4.1

USER root

# Télécharger le connecteur Elasticsearch compatible 7.16.2
RUN mkdir -p /opt/spark/jars && \
    curl -L -o /opt/spark/jars/elasticsearch-spark.jar \
    https://repo1.maven.org/maven2/org/elasticsearch/elasticsearch-spark-30_2.12/7.16.2/elasticsearch-spark-30_2.12-7.16.2.jar

WORKDIR /app

COPY sparkAnalysis.py .

CMD ["/opt/spark/bin/spark-submit", "--jars", "/opt/spark/jars/elasticsearch-spark.jar", "sparkAnalysis.py"]