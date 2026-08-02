# Professor demo (Streamlit)

## Run

From the project root (`E:\ICOT-RAG`), with the venv active:

```bash
pip install streamlit
streamlit run streamlit_app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Pages

| Page | What to show |
|------|----------------|
| **Overview** | Project pitch, KB size, facets, vs Zeng/ChatIoT |
| **Live demo** | Run facet ICOT on sample/custom questions; answer + filtered docs + trace |
| **Results** | Frozen eval tables (3-way multi-facet, ablations) |
| **How it works** | Pipeline flowchart + repo map |

## Notes

- **Results** works offline from `artifacts/evaluation/*.json`.
- **Live demo** needs `.env` (`LLM_PROVIDER=groq`, `GROQ_API_KEY=...`) and `artifacts/chroma_db`.
- First live run is slow (loads embedding model once).
