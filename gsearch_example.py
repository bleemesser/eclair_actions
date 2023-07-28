from actions.google_search.get_search_query import get_query
from actions.google_search.get_openai_query import (
    llm_clean_information,
    llm_parse,
    # llm_evaluate_info,
    llm_answer,
    # chunk_text,
)

query = "Are both the directors of Jaws and Casino Royale from the same country?"
print(query)

questions = []
iterations = 0
# recursively identify the lowest-level questions
def split_into_questions(query):
    global iterations
    global questions
    if iterations > 5:
        return
    response = llm_parse(query, questions)
    print(response)
    if response["needs_followup"]:
        for question in response["questions"]:
            # print(question, iterations)
            questions.append(question)
            split_into_questions(question)
            iterations += 1
    questions.append(query)


# get the questions
split_into_questions(query)
questions = list(set(questions))

print(questions)
# get the information
information = ""
for question in questions:
    print(question)
    info_single = get_query(question)
    info_single = llm_clean_information(info_single, question)
    info_single = [str(info["relevant_information"]) for info in info_single]
    # print(info_single[:10])
    information += " ".join(info_single)
    # response = llm_evaluate_info(information, " ".join(questions))
    # print(response)
    # # print(information)
    # if response:
info_single = llm_clean_information(information, " ".join(questions))
info_single = [str(info["relevant_information"]) for info in info_single]
information = " ".join(info_single)
with open("information.txt", "w") as f:
    f.write(information)
answer = llm_answer(information, query)
print(answer)




        
        