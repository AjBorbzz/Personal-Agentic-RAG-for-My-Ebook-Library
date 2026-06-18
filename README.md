# Notes:

### Run batch ingestion

```bash
python scripts/batch_ingest_index.py /absolute/path/to/your/ebooks --recursive
```

##### Process 5

```bash
python scripts/batch_ingest_index.py /absolute/path/to/your/ebooks --recursive --limit 5
```

##### Ingest Only, No Index

```bash
python scripts/batch_ingest_index.py /absolute/path/to/your/ebooks --recursive --no-index
```

##### Force Re-process

```bash
python scripts/batch_ingest_index.py /absolute/path/to/your/ebooks --recursive --force
```

##### Show Indexd files: 

```bash
cat data/batch_ingest_manifest.json | jq '.files[] | select(.status=="indexed") | {
  filename,
  document_id,
  status,
  ingest_response,
  index_response
}'
```




