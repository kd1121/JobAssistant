import pandas as pd
import openai
import numpy as np
import faiss
import os

# Set up your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
#openai.api_key = ""

class JobRetrieval:
    def __init__(self, data_path):
        # Load dataset
        self.df = pd.read_csv(data_path)
        self.embeddings = None
        self.index = None
        self.embedding_file = "data/job_embeddings.npy"
        self.load_embeddings()

    def load_embeddings(self):
        """Load or create embeddings for job descriptions."""
        if os.path.exists(self.embedding_file):
            # Load pre-saved embeddings
            print("Loading pre-saved embeddings...")
            self.embeddings = np.load(self.embedding_file)
        else:
            # Generate embeddings if not available
            print("Generating new embeddings...")
            self.embeddings = self.generate_embeddings(self.df['job_description'])
            os.makedirs(os.path.dirname(self.embedding_file), exist_ok=True)
            np.save(self.embedding_file, self.embeddings)

        # Create FAISS index for fast similarity search
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)

    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts using OpenAI."""
        embeddings = []
        for text in texts:
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            embeddings.append(response['data'][0]['embedding'])
        return np.array(embeddings, dtype=np.float32)

    def query(self, user_query, top_k=3):
        """Retrieve the top_k most relevant jobs for a user query."""
        # Generate query embedding
        response = openai.Embedding.create(
            input=user_query,
            model="text-embedding-ada-002"
        )
        query_embedding = response['data'][0]['embedding']

        # Search for nearest neighbors
        query_vector = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_vector, top_k)

        # Fetch job postings
        results = self.df.iloc[indices[0]].to_dict(orient="records")
        return results
    
    # def query_with_skills(self, user_query, top_k=5):
    #     """Retrieve jobs that match the query and prioritize based on skills."""
    #     # Extract skills from user query (you can use more advanced NLP techniques here)
    #     skills = [word.lower() for word in user_query.split() if len(word) > 2]

    #     # Retrieve initial results
    #     results = self.query(user_query, top_k=top_k)

    #     # Re-rank results based on skill matches
    #     def skill_match_score(job):
    #         job_skills = str(job.get("preferred_skills", "")).lower()
    #         return sum(skill in job_skills for skill in skills)

    #     ranked_results = sorted(
    #         results,
    #         key=lambda job: skill_match_score(job),
    #         reverse=True
    #     )

    #     return ranked_results

    def get_trending_jobs(self, top_k=5):
        """Analyze the dataset and return top trending jobs."""
        # Analyze job frequencies by business_title
        trending_jobs = self.df['business_title'].value_counts().head(top_k)
        

        # Prepare results as a list of dictionaries
        results = [
            {"business_title": title, "count": count}
            for title, count in trending_jobs.items()
        ]
        return results
    
    def get_trending_categories(self, top_k=5):
        """Analyze the dataset and return top trending job categories."""
        # Analyze job frequencies by category
        trending_categories = self.df['job_category'].value_counts().head(top_k)

        # Prepare results as a list of dictionaries
        results = [
            {"job_category": category, "count": count}
            for category, count in trending_categories.items()
        ]
        return results
    
    def get_trending(self, query_type="jobs", top_k=5):
        """
        Return trending jobs or categories based on the query type.
        Args:
            query_type (str): Either "jobs" or "categories".
            top_k (int): Number of top trends to return.
        """
        if query_type == "categories":
            trending_data = self.get_trending_categories(top_k)
        elif query_type == "jobs":
            trending_data = self.get_trending_jobs(top_k)
        else:
            trending_data = []
    
        return trending_data


