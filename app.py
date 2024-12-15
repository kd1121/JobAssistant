from flask import Flask, request, jsonify
from app.retrieval import JobRetrieval
import openai
import os
# from flask.json import JSONEncoder

# Initialize the Flask app
app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the retrieval system
retrieval_system = JobRetrieval(data_path="data/NYC_Jobs_Cleaned.csv")

def generate_response(user_query, retrieved_jobs=None, trends=None):
    """
    Generate a conversational response using OpenAI's GPT model.
    """
    if trends:
        # Format the trending data for GPT
        trend_details = "\n".join([
            f"{i+1}. {item['business_title'] if 'business_title' in item else item['job_category']} "
            f"({item['count']} listings)"
            for i, item in enumerate(trends)
        ])
        prompt = (
            f"You are a helpful job assistant. The user asked: '{user_query}'.\n\n"
            f"Here are the top trends:\n{trend_details}\n\n"
            f"Summarize these trends in a conversational tone."
        )
    elif retrieved_jobs:
        if not retrieved_jobs:
            return "I'm sorry, I couldn't find any jobs matching your query. Please try refining your search."
        job_summaries = "\n".join([
            f"{i+1}. {job['business_title']} at {job['agency']} - {job['work_location']}. "
            f"Salary: {job['salary_range_from']} to {job['salary_range_to']} ({job['salary_frequency']})."
            for i, job in enumerate(retrieved_jobs)
        ])
        prompt = (
            f"You are a helpful job assistant. The user asked: '{user_query}'.\n\n"
            f"Here are some relevant job postings:\n{job_summaries}\n\n"
            f"Provide a helpful response summarizing the best matches. And make the abrevation to acutual city name."
        )
    else:

        # Handle unsupported queries or ambiguous requests
        return (
            "I'm sorry, I couldn't process your query. Here are some suggestions:\n"
            "- Try searching for a specific job title or category.\n"
            "- Include a location or salary range if relevant.\n"
            "- Ask about trending jobs or categories."
        )

    # Generate GPT response
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful job assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response['choices'][0]['message']['content']


# Global variable to store conversation history
conversation_history = [
    {
        "query": "Show me software engineering jobs in New York.",
        "retrieved_jobs": [],  # List of retrieved jobs
        "response_message": "Here are some jobs for software engineers in New York."
    },
    {
        "query": "Tell me more about the first job.",
        "retrieved_jobs": [],  # Optionally store context for follow-up
        "response_message": "The first job is a Software Engineer role at XYZ."
    },
]

@app.route("/")
def home():
    return "Hello, this is your Job Assistant!"

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/query", methods=["POST"])
def query():
    global conversation_history

    user_input = request.json.get("query")
    reset_context = request.json.get("reset_context", False)

    if not user_input:
        return jsonify({"error": "Query is missing"}), 400
    
    # Reset context if requested
    if reset_context:
        conversation_history.clear()

    # Check for trend-related keywords
    if "trending" in user_input.lower():
        if "category" in user_input.lower():
            trends = retrieval_system.get_trending(query_type="categories")
        else:
            trends = retrieval_system.get_trending(query_type="jobs")

        # Generate a conversational response for trends
        response_message = generate_response(user_query=user_input, trends=trends)
        return jsonify({
            "trending": trends,
            "response_message": response_message
        })

    # If not a trend-related query, perform regular job retrieval
    retrieved_jobs = retrieval_system.query(user_input)
    conversation_history.append({
        "query": user_input,
        "retrieved_jobs": retrieved_jobs
    })

    # Generate a conversational response for retrieved jobs
    response_message = generate_response(user_query=user_input, retrieved_jobs=retrieved_jobs)
    return jsonify({
        "retrieved_jobs": retrieved_jobs,
        "response_message": response_message,
        "conversation_history": conversation_history
    })


@app.route("/follow-up", methods=["POST"])
def follow_up():
    global conversation_history

    user_input = request.json.get("query")
    if not user_input:
        return jsonify({"error": "Follow-up query is missing"}), 400

    if not conversation_history:
        return jsonify({"error": "No conversation history available"}), 400

    # Use the last retrieved jobs to answer the follow-up query
    #last_results = conversation_history[-1]["retrieved_jobs"]

    # Use the last conversation's retrieved jobs as context
    last_entry = conversation_history[-1]
    previous_query = last_entry["query"]
    previous_jobs = last_entry["retrieved_jobs"]

    follow_up_prompt = (
        #f"You are a job assistant. The user previously asked: '{conversation_history[-1]['query']}'.\n\n"

        f"You are a job assistant. The user previously asked: '{previous_query}'.\n\n"

        f"Here are the jobs that were retrieved:\n"

        #f"{[job['business_title'] for job in last_results]}\n\n"

        f"{[job['business_title'] for job in previous_jobs]}\n\n"

        f"The user now asks: '{user_input}'.\n"
        f"Provide an appropriate response based on the previous jobs and the new query."
    )

    # Generate GPT response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful job assistant."},
            {"role": "user", "content": follow_up_prompt}
        ]
    )

    response_message = response['choices'][0]['message']['content']

    # Append the follow-up to conversation history
    conversation_history.append({
        "query": user_input,
        "response_message": response_message,
        "retrieved_jobs": previous_jobs  # Optionally refine this if needed
        
    })

    return jsonify({
        "response_message": response['choices'][0]['message']['content']
    })


####################################################################################

@app.route("/trending", methods=["GET"])
def trending():
    # Get top trending jobs
    top_k = request.args.get("top_k", default=5, type=int)
    trending_jobs = retrieval_system.get_trending_jobs()
    trending_categories = retrieval_system.get_trending_categories()

    # Return the results
    return jsonify({
        "trending_jobs": trending_jobs,
        "trending_categories": trending_categories
    })

######################################################################################

@app.route("/history", methods=["GET"])
def history():
    return jsonify({"conversation_history": conversation_history})


if __name__ == "__main__":
    app.run(debug=True)
