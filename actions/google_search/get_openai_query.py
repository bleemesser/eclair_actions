import openai
import json
from langchain.text_splitter import TokenTextSplitter


class OpenAIActionLayer:
    def __init__(self):
        with open("openai_conf.json", "r") as f:
            conf = json.load(f)
            self.api_key = conf["key"]
            self.model = conf["model"]
            self.role = conf["role"]
        self.ask = self._create_service()

    def _create_service(self):
        openai.api_key = self.api_key
        # create service function that takes in a prompt and returns a response
        def service(prompt: str):
            messages = [{"role": self.role, "content": prompt}]
            response = openai.ChatCompletion.create(
                model=self.model, messages=messages, temperature=0,
            )
            return response.choices[0].message["content"]

        return service


def chunk_text(text, max_length=4096):
    text_splitter = TokenTextSplitter(chunk_size=max_length, chunk_overlap=0)
    texts = text_splitter.split_text(text)
    return texts


def llm_clean_information(input_text, query):
    base_prompt = """
    In the following query, the user is asking for information about a topic.
    You are a search engine that is given the scraped text from several websites.
    For the following query, grab any/all relevant information from the text.

    Respond in this format:
    {
        "relevant_information": "info 1, info 2, ..."
    }
    Always adhere to JSON syntax.
    
    Here is the query:
    {1}
    
    Here is the scraped text:
    {2}
    """.replace(
        "{1}", query
    )
    with open("input_text.txt", "w") as f:  # DEBUG
        f.write(input_text)

    texts = chunk_text(input_text, max_length=4096 - len(base_prompt))

    print(f"Cleaning {len(texts)} chunks")

    with open("info_pieces.txt", "w") as f:  # DEBUG
        f.write("\n\n\n.................".join(texts))

    layer = OpenAIActionLayer()
    responses = []
    for info_piece in texts:
        prompt = base_prompt.replace("{2}", info_piece)
        # print(prompt)
        response = layer.ask(prompt)
        try:
            responses.append(json.loads(response))
        except json.JSONDecodeError:
            responses.append({"relevant_information": []})
            print("JSONDecodeError")
    # print(responses)
    return responses


def llm_parse(query, previous_questions):
    prompt = """
    In the following query, the user is asking a question about a topic.
    Your job is to determine whether follow-up questions are needed and if so, what are they. Make sure not to ask 
    multiple things in one question. For example, if the user asks "How old is the president of the United States?" you should ask "Who is the current president of the United States?" -- not "How old is the president of the United States?" --
    and if the user asks "How much does the CEO of Google make?" you should ask "Who is the CEO of Google?" but not "How much does the CEO of Google make?" because there are multiple questions in that one question.
    Once the question can be answered directly, you can stop asking follow-up questions.
    Generally, you should ask follow-up questions until you can answer the question directly, it is more likely you will need to ask more than not.
    For comparison questions, always ask follow-up questions.
    For questions about people or their families, keep in mind the familial relationships between people. If asked about someone's maternal grandfather, you should ask about their mother, and then their mother's father.
    
    Respond in this format:
    {
        "needs_followup": true/false,
        "questions": ["question1", "question2", ...]
    }
    Always adhere to JSON syntax.
    
    Here is the query:
    {1}
    
    Here are questions that have already been asked, do not ask these again:
    {2}
    """.replace(
        "{1}", query
    ).replace(
        "{2}", " - ".join(previous_questions)
    )
    
    # print(prompt)
    # .replace("{2}", input_text if len(prompt + input_text) < 4096 else input_text[:4096-len(prompt)])

    layer = OpenAIActionLayer()
    response = layer.ask(prompt)
    try:
        response = json.loads(response)
    except json.JSONDecodeError:
        response = {
            "needs_followup": False,
            "questions": [],
        }  # for now, just return empty list
        print("JSONDecodeError")
    return response


def llm_evaluate_info(input_text, query):
    base_prompt = """
    You are a search engine that is given a summary of a topic and a set of queries.
    Determine whether the information in the summary is sufficient to answer all parts of the query.

    Respond in this format:
    {
        "is_sufficient": true/false
    }
    Always adhere to JSON syntax.
    
    Here are the questions
    {1}
    
    Here is the summary:
    {2}
    """.replace(
        "{1}", query
    )

    texts = chunk_text(input_text, max_length=4096 - len(base_prompt))
    print(f"Evaluating {len(texts)} chunks")
    layer = OpenAIActionLayer()
    responses = []
    for info_piece in texts:
        prompt = base_prompt.replace("{2}", info_piece)
        response = layer.ask(prompt)
        try:
            responses.append(json.loads(response))
        except json.JSONDecodeError:
            responses.append({"is_sufficient": False})
            print("JSONDecodeError")
    return any(res["is_sufficient"] for res in responses)


def llm_answer(input_text, query):
    prompt = """
    You are a search engine that is given a summary of some information that is relevant to the query, and the query.
    Answer the query using the information in the summary. Respond directly and include all relevant information. If
    the query is a comparison, answer the query by comparing the two things. If the query is a question, answer the
    question.
    
    Respond in this format:
    {
        "answer": "answer"
    }
    Always adhere to JSON syntax.
    
    Here is the query:
    {1}
    
    Here is the summary:
    {2}
    """.replace(
        "{1}", query
    )

    prompt = prompt.replace(
        "{2}",
        input_text
        if len(prompt + input_text) < 4096
        else input_text[: 4096 - len(prompt)],
    )

    layer = OpenAIActionLayer()
    response = layer.ask(prompt)
    try:
        response = json.loads(response)
    except json.JSONDecodeError:
        response = {"answer": False}
        print("JSONDecodeError")
    return response
