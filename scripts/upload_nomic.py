import os
import sys
from pathlib import Path

import chromadb
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    db_path = Path("data/chroma")
    if not db_path.exists():
        print("Error: ChromaDB not found in data/chroma/")
        sys.exit(1)

    print("Loading ChromaDB collection 'posts'...")
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_collection("posts")
    
    res = collection.get(include=["embeddings", "metadatas"])
    
    embeddings = res.get("embeddings")
    metadatas = res.get("metadatas")
    
    if embeddings is None or len(embeddings) == 0 or metadatas is None or len(metadatas) == 0:
        print("Collection is empty. Run embedding pipeline first.")
        sys.exit(1)
        
    print(f"Loaded {len(embeddings)} embeddings.")
    
    nomic_key = os.environ.get("NOMIC_API_KEY")
    
    url_out_path = Path("data/nomic_url.txt")
    url_out_path.parent.mkdir(parents=True, exist_ok=True)
    
    if nomic_key:
        print("NOMIC_API_KEY found. Uploading to Nomic Atlas...")
        import nomic
        from nomic import atlas
        
        nomic.login(nomic_key)
        
        metadata_list = []
        for m in metadatas:
            text = str(m.get("text", ""))
            metadata_list.append({
                "post_id": m.get("post_id", ""),
                "text": text[:200] + ("..." if len(text) > 200 else ""),
                "author": m.get("author", "Unknown"),
                "platform": m.get("platform", "Unknown")
            })
            
        try:
            map_info = atlas.map_embeddings(
                embeddings=np.array(embeddings, dtype=np.float32),
                data=metadata_list,
                id_field="post_id",
                name="narrativetrace-simppl",
                description="Russian state media amplification on Reddit and Twitter 2022"
            )
            map_url = map_info.map_link
            print(f"Upload complete. Map URL: {map_url}")
            
            with open(url_out_path, "w", encoding="utf-8") as f:
                f.write(map_url)
                
        except Exception as e:
            print(f"Nomic upload failed: {e}")
            sys.exit(1)
            
    else:
        print("NOMIC_API_KEY not set. Generating local DataMapPlot...")
        import datamapplot
        import umap
        import hdbscan
        
        print("Reducing dimensions with UMAP (min_dist=0.1)...")
        coords = umap.UMAP(n_components=2, metric="cosine", min_dist=0.1, random_state=42).fit_transform(embeddings)
        
        print("Clustering with HDBSCAN...")
        clusterer = hdbscan.HDBSCAN(min_cluster_size=15).fit(coords)
        cluster_labels = clusterer.labels_
        
        # Build text string labels mapped appropriately
        labels = np.array([f"Cluster {l}" if l != -1 else "Unclustered Noise" for l in cluster_labels], dtype=object)
        
        viz_path = Path("frontend/public/embedding_viz.html")
        viz_path.parent.mkdir(parents=True, exist_ok=True)
        
        print("Creating interactive plot...")
        hover_text = [m.get("text", "")[:150] for m in metadatas]
        
        plot = datamapplot.create_interactive_plot(
            coords, 
            labels,
            hover_text=hover_text,
            title="NarrativeTrace Embedding Map (Local)"
        )
        plot.save(str(viz_path))
        print(f"Saved local interactive HTML plot to {viz_path}")
        
        with open(url_out_path, "w", encoding="utf-8") as f:
            f.write("local")
        print("Saved 'local' to data/nomic_url.txt")


if __name__ == "__main__":
    main()
