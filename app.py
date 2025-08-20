from flask import Flask, request, jsonify, render_template
from app.retrieval import JobRetrieval
import openai
import os
import json
# from flask.json import JSONEncoder
CONVERSATION_HISTORY_JSON = "data/conversation_history.json"

def save_to_json(conversation_history):
    # Save the entire conversation history to a JSON file
    with open(CONVERSATION_HISTORY_JSON, "w", encoding="utf-8") as file:
        json.dump(conversation_history, file, ensure_ascii=False, indent=4)

# Initialize the Flask app
app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
#openai.api_key = ""
conversation_history = []  # To store the chat context

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
            f"Summarize these trends in a conversational tone. And make fill up some wordy gaps if it is there."
        )
    elif retrieved_jobs:
        if not retrieved_jobs:
            return "I'm sorry, I couldn't find any jobs matching your query. Please try refining your search."
        job_summaries = "\n".join([
            f"{i+1}. {job['business_title']} at {job['agency']} - {job['work_location']}. "
            f"Salary: {job['salary_range_from']} to {job['salary_range_to']} ({job['salary_frequency']})."
            f"Job Description: {job['job_description']}"
            for i, job in enumerate(retrieved_jobs)
        ])
        prompt = (
            f"You are a helpful job assistant. The user asked: '{user_query}'.\n\n"
            f"Here are some relevant job postings:\n{job_summaries}\n\n"
            f"Provide a helpful response summarizing the best matches. And make the abrevation to acutual city name.\n\n"
            f"NOTE: even you are a helpful job assistant is user asked irrelavent information or that is not actual, You can simply appologise and do not need to consider job postings.\n"
            f"Only give Job description if and only if User asked something related to Job description."
            f"If user asked something like hello msg than you should give Response as a Welcoming way."
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
            {"role": "system", "content": "You are a helpful job assistant.."},
            {"role": "user", "content": prompt}
        ]
    )

    return response['choices'][0]['message']['content']

@app.route("/")
def index():
    return render_template("index.html")
   
# @app.route("/query", methods=["POST"])
# def query():
#     global conversation_history

#     user_input = request.json.get("query")
#     history = request.json.get("history", [])
#     reset_context = request.json.get("reset_context", False)

#     if not user_input:
#         return jsonify({"error": "Query is missing"}), 400
    
#     # Reset context if requested
#     if reset_context:
#         conversation_history.clear()

#     # Determine if this is a follow-up query
#     if "follow-up" "tell me more" in user_input.lower() and history:
#         last_jobs = history[-1].get("retrieved_jobs", [])
#         follow_up_prompt = (
#             f"The user previosly asked: '{history[-1]['user']}' .\n\n"
#             f"Here are the jobs that were retrieved: \n"
#             f"{[job['business_title'] for job in last_jobs]}\n\n"
#             f"The user now asks: '{user_input}. \n\n"
#             f"Provide an appropriate response based on the previos jobs and the new query.\n"
#             f"You should generate only those things which are asked and which are in jobs were retrieved."
#         )

#         response = openai.ChatCompletion.create(
#             model = "gpt-4",
#             messages = [
#                 {"role": "system", "content": "You are a helpful job assistant."},
#                 {"role": "user", "content": follow_up_prompt},
#             ],
#         )
#         response_message = response['choices'][0]['message']['content']
#         return jsonify({"response_message": response_message, "conversation_history": history})

#     # Check for trend-related keywords
#     if "trending" in user_input.lower():
#         if "category" in user_input.lower():
#             trends = retrieval_system.get_trending(query_type="categories")
#         else:
#             trends = retrieval_system.get_trending(query_type="jobs")

#         # Generate a conversational response for trends
#         response_message = generate_response(user_query=user_input, trends=trends)
#         return jsonify({
#             "trending": trends,
#             "response_message": response_message
#         })

#     # If not a trend-related query, perform regular job retrieval
#     retrieved_jobs = retrieval_system.query(user_input)
#     conversation_history.append({
#         "query": user_input,
#         "retrieved_jobs": retrieved_jobs
#     })

#     # Generate a conversational response for retrieved jobs
#     response_message = generate_response(user_query=user_input, retrieved_jobs=retrieved_jobs)
#     return jsonify({
#         "retrieved_jobs": retrieved_jobs,
#         "response_message": response_message,
#         "conversation_history": conversation_history
#     })

# @app.route("/query", methods=["POST"])
# def query():
#     global conversation_history

#     # Debugging: Log the incoming request payload
#     print("Incoming request data:", request.json)

#     data = request.json
#     if not data:
#         return jsonify({"error": "No data provided"}), 400
    

#     user_input = data.get("query")
#     history = data.get("history", [])
#     reset_context = data.get("reset_context", False)

#     if not user_input:
#         return jsonify({"error": "Query is missing"}), 400

#     if not user_input:
#         return jsonify({"error": "Query is missing"}), 400

#     # Reset context if requested
#     if reset_context:
#         conversation_history.clear()
#         save_to_json(conversation_history)
#         return jsonify({"response_message:" "Context has been reset."})

#     # Determine if this is a follow-up query
#     if "tell me more" in user_input.lower() in user_input.lower():
#         if not history:
#             return jsonify({"error": "No conversation history available for follow-up."}), 400

#         # Retrieve the last retrieved jobs and previous query
#         last_entry = history[-1]
#         previous_query = last_entry.get("query", "")
#         previous_jobs = last_entry.get("retrieved_jobs", [])
        
#         # Ensure the retrieved jobs contain valid data
#         if not previous_jobs or len(previous_jobs) == 0:
#             return jsonify({"error": "No retrieved jobs available for follow-up."}), 400

#         # Build a follow-up prompt
#         #first_job = previous_jobs[0]
#         follow_up_prompt = (
#             f"You are a job assistant. The user previously asked: '{previous_query}'.\n\n"
#             f"Here are the jobs that were retrieved:\n"
#             f"{[job['business_title'] for job in previous_jobs]}\n\n"
#             f"The user now asks: '{user_input}'.\n"
#             f"Provide an appropriate response based on the previous jobs and the new query."
#         )

#         # Generate GPT response
#         response = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You are a helpful job assistant."},
#                 {"role": "user", "content": follow_up_prompt}
#             ]
#         )
#         response_message = response['choices'][0]['message']['content']
#         print("Retrieved Jobs:", retrieved_jobs)

#         # Update conversation history
#         conversation_history.append({
#             "query": user_input,
#             "response_message": response_message,
#             "retrieved_jobs": previous_jobs  # Optionally include context jobs
#         })

#         #print("Updated Conversation History:", conversation_history)

#         return jsonify({
#             "response_message": response_message,
#             "conversation_history": conversation_history
#         })


#     # Handle general queries
#     retrieved_jobs = retrieval_system.query(user_input)

#     # Update conversation history
#     conversation_history.append({
#         "query": user_input,
#         "retrieved_jobs": retrieved_jobs,
#         "response_message": None
#     })
    

#     # Generate a conversational response for retrieved jobs
#     response_message = generate_response(user_query=user_input, retrieved_jobs=retrieved_jobs)
#     conversation_history[-1]["response_message"] = response_message

#     # Save updated history to JSON
#     save_to_json(conversation_history)


#     return jsonify({
#         "retrieved_jobs": retrieved_jobs,
#         "response_message": response_message,
#         "conversation_history": conversation_history
#     })

@app.route("/query", methods=["POST"])
def query():
    data = request.json
    user_query = data.get("query")
    last_jobs = data.get("last_jobs", [])  # Received from the frontend

    if not user_query:
        return jsonify({"error": "Query is missing"}), 400

    # Handle follow-up queries
    if "tell me more" in user_query.lower():
        if not last_jobs:
            return jsonify({
                "response_message": "I don't have details from your previous query. Please ask again or provide more specifics."
            }), 400

        # Build a follow-up prompt
        follow_up_prompt = (
            f"The user previously retrieved the following jobs:\n"
            f"{[job['business_title'] for job in last_jobs]}\n\n"
            f"The user now asks: '{user_query}'.\n"
            f"Provide an appropriate response based on these jobs and the new query."
        )

        # Generate GPT response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful job assistant."},
                {"role": "user", "content": follow_up_prompt}
            ]
        )
        response_message = response['choices'][0]['message']['content']

        return jsonify({
            "response_message": response_message
        })
    
    # Handle trending or category queries
    if "trending" in user_query.lower():
        query_type = "categories" if "category" in user_query.lower() else "jobs"
        trends = retrieval_system.get_trending(query_type=query_type)

        # Generate a conversational response for trends
        response_message = generate_response(user_query=user_query, trends=trends)

        return jsonify({
            "trending": trends,
            "response_message": response_message
        })


    # Handle general queries
    retrieved_jobs = retrieval_system.query(user_query)
    response_message = generate_response(user_query=user_query, retrieved_jobs=retrieved_jobs)

    return jsonify({
        "retrieved_jobs": retrieved_jobs,
        "response_message": response_message
    })




# @app.route("/follow-up", methods=["POST"])
# def follow_up():
#     global conversation_history

#     user_input = request.json.get("query")
#     if not user_input:
#         return jsonify({"error": "Follow-up query is missing"}), 400

#     if not conversation_history:
#         return jsonify({"error": "No conversation history available"}), 400

#     # Use the last retrieved jobs to answer the follow-up query
#     #last_results = conversation_history[-1]["retrieved_jobs"]

#     # Use the last conversation's retrieved jobs as context
#     last_entry = conversation_history[-1]
#     previous_query = last_entry["query"]
#     previous_jobs = last_entry["retrieved_jobs"]

#     follow_up_prompt = (
#         #f"You are a job assistant. The user previously asked: '{conversation_history[-1]['query']}'.\n\n"

#         f"You are a job assistant. The user previously asked: '{previous_query}'.\n\n"

#         f"Here are the jobs that were retrieved:\n"

#         #f"{[job['business_title'] for job in last_results]}\n\n"

#         f"{[job['business_title'] for job in previous_jobs]}\n\n"

#         f"The user now asks: '{user_input}'.\n"
#         f"Provide an appropriate response based on the previous jobs and the new query."
#     )

#     # Generate GPT response
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are a helpful job assistant."},
#             {"role": "user", "content": follow_up_prompt}
#         ]
#     )

#     response_message = response['choices'][0]['message']['content']

#     # Append the follow-up to conversation history
#     conversation_history.append({
#         "query": user_input,
#         "response_message": response_message,
#         "retrieved_jobs": previous_jobs  # Optionally refine this if needed
        
#     })

#     return jsonify({
#         "response_message": response['choices'][0]['message']['content']
#     })



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


@app.route("/history", methods=["GET"])
def history():
    return jsonify({"conversation_history": conversation_history})


if __name__ == "__main__":
    # Use the port provided by Render, or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
