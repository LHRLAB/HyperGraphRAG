import re
import json
import os
os.environ["OPENAI_API_KEY"] = open("openai_api_key.txt").read().strip()
from openai import OpenAI
import argparse
from tqdm import tqdm


def batch_eval(query_file, result1_file, result2_file, output_file_path, output_score_path):
    client = OpenAI()

    with open(query_file, "r") as f:
        data = f.read()

    queries = re.findall(r"- Question \d+: (.+)", data)

    with open(result1_file, "r") as f:
        answers1 = json.load(f)
    answers1 = [i["result"] for i in answers1]

    with open(result2_file, "r") as f:
        answers2 = json.load(f)
    answers2 = [i["result"] for i in answers2]

    results = []
    for i, (query, answer1, answer2) in enumerate(tqdm(zip(queries, answers1, answers2))):
        sys_prompt = """
        ---Role---
        You are an expert tasked with evaluating two answers to the same question based on four criteria: **Factuality**, **Comprehensiveness**, **Diversity**, and **Empowerment**.
        """

        prompt = f"""
        You will evaluate two answers to the same question based on four criteria: **Factuality**, **Comprehensiveness**, **Diversity**, and **Empowerment**.

        - **Factuality**: How accurate is the information provided in the answer, and does it align with verifiable facts and evidence?
        - **Comprehensiveness**: How much detail does the answer provide to cover all aspects and details of the question?
        - **Diversity**: How varied and rich is the answer in providing different perspectives and insights on the question?
        - **Empowerment**: How well does the answer help the reader understand and make informed judgments about the topic?

        For each criterion, choose the better answer (either Answer 1 or Answer 2) and explain why. Then, select an overall winner based on these four categories.

        Here is the question:
        {query}

        Here are the two answers:

        **Answer 1:**
        {answer1}

        **Answer 2:**
        {answer2}

        Evaluate both answers using the four criteria listed above and provide detailed explanations for each criterion.

        Output your evaluation in the following JSON format:

        {{
            "Factuality": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Provide explanation here]"
            }},
            "Comprehensiveness": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Provide explanation here]"
            }},
            "Diversity": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Provide explanation here]"
            }},
            "Empowerment": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Provide explanation here]"
            }},
            "Overall Winner": {{
                "Winner": "[Answer 1 or Answer 2]",
                "Explanation": "[Summarize why this answer is the overall winner based on the four criteria]"
            }}
        }}
        """

        # 调用 OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "Factuality": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The answer that is better in terms of factual accuracy (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A detailed explanation of why the chosen answer is better in terms of factual accuracy, including references to specific facts or evidence if applicable."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            },
                            "Comprehensiveness": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The answer that is better in terms of comprehensiveness (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A detailed explanation of why the chosen answer is better in terms of comprehensiveness."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            },
                            "Diversity": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The answer that is better in terms of diversity (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A detailed explanation of why the chosen answer is better in terms of diversity."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            },
                            "Empowerment": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The answer that is better in terms of empowerment (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A detailed explanation of why the chosen answer is better in terms of empowerment."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            },
                            "Overall Winner": {
                                "type": "object",
                                "properties": {
                                    "Winner": {
                                        "type": "string",
                                        "description": "The overall better answer based on all four criteria (Answer 1 or Answer 2).",
                                        "enum": ["Answer 1", "Answer 2"]
                                    },
                                    "Explanation": {
                                        "type": "string",
                                        "description": "A summary of why the chosen answer is the overall winner."
                                    }
                                },
                                "required": ["Winner", "Explanation"],
                                "additionalProperties": False
                            }
                        },
                        "required": ["Factuality", "Comprehensiveness", "Diversity", "Empowerment", "Overall Winner"],
                        "additionalProperties": False
                    }
                }
            }
        )
        # 解析结果
        evaluation = response.choices[0].message.content
        print(f"Question {i+1} evaluation completed.\n")
        
        try:
            # 保存结果
            results.append({"Question": query, "Answer1": answer1, "Answer2": answer2, "Evaluation": json.loads(evaluation)})
        except:
            print(f"Error in question {i+1}")

    # 计算四种指标两个答案的得分, 
    answer_scores = {"Factuality": {"Answer1":0.0,"Answer2":0.0}, "Comprehensiveness": {"Answer1":0.0,"Answer2":0.0}, "Diversity": {"Answer1":0.0,"Answer2":0.0}, "Empowerment": {"Answer1":0.0,"Answer2":0.0}, "Overall Winner": {"Answer1":0.0,"Answer2":0.0}}

    temp_results = []
    for result in results:
        try:
            evaluation = result["Evaluation"]
            for key in evaluation:
                if evaluation[key]["Winner"] == "Answer 1":
                    pass
                elif evaluation[key]["Winner"] == "Answer 2":
                    pass
            if "Factuality" in evaluation and "Comprehensiveness" in evaluation and "Diversity" in evaluation and "Empowerment" in evaluation and "Overall Winner" in evaluation:
                temp_results.append(result)
        except:
            print(f"Error in question {i+1}")
    results = temp_results

    for result in results:
        evaluation = result["Evaluation"]
        for key in evaluation:
            if evaluation[key]["Winner"] == "Answer 1":
                answer_scores[key]['Answer1'] += 1.0/len(results)
            elif evaluation[key]["Winner"] == "Answer 2":
                answer_scores[key]['Answer2'] += 1.0/len(results)
    
    # 将所有结果写入文件
    with open(output_file_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"All evaluations completed and saved to {output_file_path}")
    
    # 将得分写入文件
    # with open(output_score_path, "w") as f:
    #     json.dump(answer_scores, f, indent=2)
        
    # print(f"All scores saved to {output_score_path}")
    
    return answer_scores

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query_file", type=str, default="datasets/ultradoman/questions/hypertension_questions.txt")
    parser.add_argument("--result1_file", type=str, default="output_qual/ultradoman/hypertension/hypertension_result.json")
    parser.add_argument("--result2_file", type=str, default="others/LightRAG/output_qual/ultradoman/hypertension/hypertension_result.json")
    parser.add_argument("--output_file_path", type=str, default="output_qual/ultradoman/hypertension/batch_eval.jsonl")
    parser.add_argument("--output_score_path", type=str, default="output_qual/ultradoman/hypertension/batch_eval_scores.json")
    args = parser.parse_args()
    score1 = batch_eval(args.query_file, args.result1_file, args.result2_file, args.output_file_path, args.output_score_path)
    score2 = batch_eval(args.query_file, args.result2_file, args.result1_file, args.output_file_path, args.output_score_path)
    
    answer_scores = {"Factuality": {"Answer1":0.0,"Answer2":0.0}, "Comprehensiveness": {"Answer1":0.0,"Answer2":0.0}, "Diversity": {"Answer1":0.0,"Answer2":0.0}, "Empowerment": {"Answer1":0.0,"Answer2":0.0}, "Overall Winner": {"Answer1":0.0,"Answer2":0.0}}
    # 计算两个模型的得分
    for key in answer_scores:
        answer_scores[key]["Answer1"] = (score1[key]["Answer1"] + score2[key]["Answer2"])/2
        answer_scores[key]["Answer2"] = (score1[key]["Answer2"] + score2[key]["Answer1"])/2
    
    print(answer_scores)
    
    # 将得分写入文件
    with open(args.output_score_path, "w") as f:
        json.dump(answer_scores, f, indent=2)
        
    print(f"All scores saved to {args.output_score_path}")
