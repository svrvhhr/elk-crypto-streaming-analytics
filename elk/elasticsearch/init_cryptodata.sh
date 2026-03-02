#!/usr/bin/env sh
set -eu

ES_URL="http://elasticsearch:9200"
INDEX="cryptodata"

echo "⏳ Waiting for Elasticsearch..."
until curl -s "$ES_URL" >/dev/null; do
  sleep 2
done
echo "✅ Elasticsearch is up"

# Si l'index existe déjà, on ne fait rien
if [ "$(curl -s -o /dev/null -w "%{http_code}" -I "$ES_URL/$INDEX")" = "200" ]; then
  echo "ℹ️ Index $INDEX already exists. Skipping creation."
  exit 0
fi

echo "📌 Creating index $INDEX with mapping + edge_ngram..."
curl -s -X PUT "$ES_URL/$INDEX" \
  -H "Content-Type: application/json" \
  --data-binary "@/init/cryptodata.json"

echo "\n✅ Index $INDEX created."