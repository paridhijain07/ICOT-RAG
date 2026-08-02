from rag_icot.components.document_text import extract_cves
from rag_icot.components.embedding_builder import EmbeddingBuilder
from rag_icot.components.vector_store import VectorStore
from rag_icot.constants.evidence_facets import FACET_FILTERS


class Retriever:

    def __init__(self):

        self.embedding_builder = EmbeddingBuilder()

        self.vector_store = VectorStore()

        self.collection = self.vector_store.client.get_collection(
            "icot_knowledge"
        )

        self.vector_store.collection = self.collection

    def _build_where(
        self,
        source=None,
        document_type=None,
        facet=None
    ):

        if facet and facet in FACET_FILTERS:
            filters = dict(FACET_FILTERS[facet])
            source = filters.get("source", source)
            document_type = filters.get(
                "document_type",
                document_type
            )

        clauses = []

        if source:
            clauses.append({"source": source})

        if document_type:
            clauses.append({"document_type": document_type})

        if not clauses:
            return None

        if len(clauses) == 1:
            return clauses[0]

        return {"$and": clauses}

    def _exact_cve_hits(self, query, exclude_ids=None):
        """Pull metadata-exact CVE matches (dense search misses rare IDs)."""

        exclude_ids = set(exclude_ids or [])
        hits = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        for cve in extract_cves(query):
            try:
                result = self.collection.get(
                    where={"cve": cve},
                    include=["documents", "metadatas"],
                )
            except Exception:
                continue

            for doc_id, doc, meta in zip(
                result.get("ids") or [],
                result.get("documents") or [],
                result.get("metadatas") or [],
            ):
                if doc_id in exclude_ids or doc_id in hits["ids"]:
                    continue
                hits["ids"].append(doc_id)
                hits["documents"].append(doc)
                hits["metadatas"].append(meta or {})
                # Prefer exact ID matches over semantic neighbors
                hits["distances"].append(0.0)

        return hits

    def retrieve(
        self,
        query,
        k=5,
        exclude_ids=None,
        source=None,
        document_type=None,
        facet=None
    ):
        """Semantic retrieve with optional source/facet filter and ID exclusion."""

        exclude_ids = set(exclude_ids or [])

        where = self._build_where(
            source=source,
            document_type=document_type,
            facet=facet
        )

        exact = self._exact_cve_hits(query, exclude_ids=exclude_ids)

        query_embedding = self.embedding_builder.embed(query)

        # Over-fetch so we can drop already-seen documents
        fetch_k = k + len(exclude_ids) + len(exact["ids"]) + 5

        results = self.vector_store.search(
            query_embedding,
            k=fetch_k,
            where=where
        )

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = (
            results.get("distances", [[]])[0]
            if results.get("distances")
            else [None] * len(ids)
        )

        filtered = {
            "ids": [list(exact["ids"])],
            "documents": [list(exact["documents"])],
            "metadatas": [list(exact["metadatas"])],
            "distances": [list(exact["distances"])],
        }
        seen = set(exact["ids"]) | exclude_ids

        for doc_id, doc, meta, dist in zip(
            ids,
            documents,
            metadatas,
            distances
        ):
            if doc_id in seen:
                continue

            filtered["ids"][0].append(doc_id)
            filtered["documents"][0].append(doc)
            filtered["metadatas"][0].append(meta or {})
            filtered["distances"][0].append(dist)
            seen.add(doc_id)

            if len(filtered["ids"][0]) >= k:
                break

        # Trim in case exact matches already filled k
        for key in filtered:
            filtered[key][0] = filtered[key][0][:k]

        # Fallback: if source/facet filter returned nothing useful, retry unfiltered
        if not filtered["ids"][0] and where is not None:
            return self.retrieve(
                query,
                k=k,
                exclude_ids=exclude_ids,
                source=None,
                document_type=None,
                facet=None
            )

        return filtered
