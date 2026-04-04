# Qdrant Setup Specs

This document summarizes the recommended hardware and storage specs for using `Qdrant` in this repository.

It is tailored to:

- the current project stage
- the current dataset in `cob_mock_kb_large/very_large_mixed_kb`
- a local-first RAG implementation for `kb_answer`

It also separates:

- local development recommendations
- production expectations

## Scope

The current likely RAG corpus for this project is:

- `faqs/faqs.jsonl`
- `documents/*.md`
- selected chunks from `structured/structured_data.json`

That means the first working index will probably be in the range of:

- roughly `10,000` to `30,000` chunks for an initial version

This is not a huge workload for Qdrant.

## Key Qdrant Sizing Principles

Qdrant’s official capacity planning guidance gives this rough RAM estimate when vectors are kept in memory:

`memory_size = number_of_vectors * vector_dimension * 4 bytes * 1.5`

The extra `1.5x` factor is meant to account for:

- metadata
- indexes
- point versions
- temporary optimization overhead

Important practical implications:

- RAM usage grows linearly with vector count and dimension
- payload fields and payload indexes also consume memory
- if vectors are stored on disk with memmap, RAM needs can be reduced
- disk speed matters a lot when using on-disk vectors

## Example Memory Estimates

These are approximate vector-memory calculations only. They do not include all payload and system overhead.

### With `1536`-dimension embeddings

- `20,000` vectors: about `184 MB`
- `30,000` vectors: about `276 MB`
- `100,000` vectors: about `922 MB`
- `1,000,000` vectors: about `9.2 GB`

### With `768`-dimension embeddings

- `20,000` vectors: about `92 MB`
- `30,000` vectors: about `138 MB`
- `100,000` vectors: about `461 MB`
- `1,000,000` vectors: about `4.6 GB`

These numbers show why your current project does not need huge specs for the first version.

## Local Development Specs

## Minimum Local Setup

Use this only for early experimentation:

- CPU: `2` vCPU
- RAM: `4 GB`
- Storage: `20-30 GB` free SSD space
- Architecture: `64-bit` only

This is enough if:

- you are indexing a small subset first
- you are testing basic retrieval
- concurrency is very low

Tradeoffs:

- indexing may feel slower
- on-disk vectors may be preferable if RAM is tight
- large batches or many simultaneous searches may feel sluggish

## Recommended Local Setup

This is the best default for your current repo:

- CPU: `4` vCPU
- RAM: `8 GB`
- Storage: `30-50 GB` SSD or NVMe
- Architecture: `x86_64/amd64` or `arm64`

This is recommended because it gives enough room for:

- Qdrant
- the application itself
- Python processes
- embeddings generation
- normal indexing overhead
- iterative development without constant memory pressure

This is the sweet spot for:

- local ingestion of the first RAG corpus
- filtered search
- evaluation and debugging
- moderate re-indexing work

## Comfortable Local Setup

Use this if you want more headroom:

- CPU: `6-8` vCPU
- RAM: `16 GB`
- Storage: `50+ GB` NVMe

This becomes useful when:

- you index more of the dataset
- you test different embedding models
- you run repeated rebuilds
- you add reranking or hybrid retrieval
- you keep more vectors in RAM for speed

## Local Storage Guidance

Qdrant’s installation docs state that for persistent storage it requires:

- block-level access
- a POSIX-compatible file system

The docs also say:

- `NFS` is not supported
- object storage such as `S3` is not supported as the storage layer
- `SSD` or `NVMe` is recommended if vectors are offloaded to local disk

So for local work:

- use local SSD/NVMe
- do not use network file systems for the Qdrant storage path

## Local Configuration Recommendation For This Repo

For the current repo, the practical local starting point is:

- `4` vCPU
- `8 GB` RAM
- `30+ GB` SSD

Recommended mode:

- use persisted local mode, not only in-memory mode
- keep the first collection small and focused
- consider on-disk vectors only if RAM becomes tight

## Production Setup Expectations

Production specs depend on:

- total vector count
- embedding dimension
- payload size
- payload indexes
- query concurrency
- latency targets
- replication settings
- whether vectors are kept in RAM or on disk

Because of that, there is no single production number that is always correct.

Still, for this task, we can define practical production tiers.

## Small Production Setup

Use this for:

- a pilot deployment
- one tenant or small internal usage
- light to moderate query traffic

Suggested specs:

- CPU: `4-8` vCPU
- RAM: `8-16 GB`
- Storage: `100+ GB` SSD/NVMe
- Replication: `1` replica to start, depending on availability needs

This works well if:

- the index size stays modest
- concurrency is low or moderate
- some vectors or payload stay on disk

## Recommended Production Setup

Use this for:

- a serious production service
- moderate traffic
- more stable latency expectations

Suggested specs:

- CPU: `8-16` vCPU
- RAM: `16-32 GB`
- Storage: `200+ GB` NVMe
- Deployment: containerized deployment or managed Qdrant
- Replication: `2+` replicas if availability matters

This is a good target when:

- you want more vectors in RAM
- you expect heavier filtering
- you care about more stable latency under load
- you want room for growth without immediate resizing

## Higher-Scale Production Setup

Use this when:

- the corpus grows much larger
- traffic becomes significant
- low latency matters under concurrency
- you introduce more collections, tenants, or heavier filters

Suggested specs:

- CPU: `16+` vCPU
- RAM: `32-64+ GB`
- Storage: high-IOPS NVMe
- Replication: multi-node setup
- Scaling: shard and replication planning based on workload

This tier is usually unnecessary for the current stage of this repo.

## RAM-Optimized vs Storage-Optimized Setup

Qdrant officially describes two common directions:

- performance-optimized
- storage-optimized

### Performance-Optimized

Choose this when:

- you want low latency
- you want more vectors in RAM
- traffic is higher

Specs trend toward:

- more RAM
- enough CPU for indexing and search
- fast local SSD/NVMe

For this repo, that usually means:

- local: `8-16 GB` RAM
- production: `16-32 GB` RAM or more

### Storage-Optimized

Choose this when:

- cost matters more than peak speed
- you can tolerate somewhat slower queries
- vectors are stored on disk using memmap

Specs trend toward:

- fast SSD/NVMe being especially important
- lower RAM than fully in-memory setups

Important official guidance:

- if you use on-disk vector storage with slow disks, requests may become slow or time out
- Qdrant recommends local SSDs with at least `50k IOPS` when on-disk vector storage is used and performance matters

## What I Recommend For This Project

## Right Now

For the first RAG version in this repository:

- CPU: `4` vCPU
- RAM: `8 GB`
- Storage: `30-50 GB` SSD/NVMe
- Mode: local persisted Qdrant

This is enough to:

- ingest the first KB subset
- test retrieval quality
- store metadata-rich vectors
- develop `kb_answer` safely

## If You Move Toward Production

Start planning for:

- CPU: `8-16` vCPU
- RAM: `16-32 GB`
- Storage: `100-200+ GB` NVMe
- Replication and backups
- either self-hosted production deployment or managed Qdrant

## Final Takeaway

For this dataset and current project stage:

- local setup does not need huge specs
- `8 GB RAM + SSD` is a very solid starting point
- `16 GB RAM` gives comfortable headroom
- production sizing depends much more on latency and concurrency goals than on the current dataset alone

If you want one practical rule:

- local dev: `4 vCPU / 8 GB RAM / SSD`
- early production: `8 vCPU / 16 GB RAM / NVMe`

## Sources

Official Qdrant documentation used for this guidance:

- Capacity Planning: https://qdrant.tech/documentation/guides/capacity-planning/
- Installation Requirements: https://qdrant.tech/documentation/guides/installation/
- Database Optimization FAQ: https://qdrant.tech/documentation/faq/database-optimization/
- Storage: https://qdrant.tech/documentation/storage/
- Optimize Performance: https://qdrant.tech/documentation/guides/optimize/
- Bulk Upload: https://qdrant.tech/documentation/database-tutorials/bulk-upload/

## Notes

- The resource numbers above are engineering recommendations, not hard vendor requirements.
- Exact production sizing should be validated with your real embedding model, payload size, filters, and expected traffic.
- If you change to a much larger embedding dimension, memory needs will rise proportionally.
