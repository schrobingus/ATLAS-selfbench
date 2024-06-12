import os, sys
# TODO: add garbage collection, you're gonna need it
import copy
from typing import Any, Dict, List
import json

import litellm
litellm.drop_params = True

def define_structure(input_dir: str, output_dir: str, principles: List[str], categories: List[str]) -> List[str]:
    output_dir_path = os.path.join(os.getcwd(), output_dir)
    if not os.path.isdir(output_dir_path):
        os.mkdir(output_dir_path)
    for subdir in ['principles', 'principles/boosting', 'principles/correctness']:
        desired_dir = os.path.join(output_dir_path, subdir)
        os.makedirs(desired_dir, exist_ok=True)
    templates_needed = []
    for category in categories:
        category_dir = os.path.join(os.getcwd(), input_dir, 'principles', category)
        category_principles = os.listdir(category_dir)
        for test_type in ['w', 'wo']:
            base_file = f"{test_type}_principle.json"
            if base_file in category_principles:
                templates_needed.append(f"principles/{category}/{base_file}")
            for principle in principles:
                principle_file = f"{test_type}_principle_{principle}.json"
                if principle_file in category_principles:
                    templates_needed.append(f"principles/{category}/{principle_file}")
    return templates_needed

def create_template(input_dir: str, output_dir: str, models_to_use: List[str], template_needed: str) -> List[Dict[str, Any]]:
    with open(f"{input_dir}/{template_needed}", "r") as file:
        template_base = json.load(file)
    model_base = "gpt4"
    prompts_used = []
    for conv in reversed(template_base):
        if conv["model"] != model_base or conv["conversations"][0]["value"] in prompts_used:
            template_base.remove(conv)
        else:
            prompts_used.insert(-1, conv["conversations"][0]["value"])
            conv["conversations"] = [msg for msg in conv["conversations"] if msg["from"] != "gpt"]
    template: List[Dict[str, Any]] = []
    template = [
        {**copy.deepcopy(conv_raw), "model": model, "id": f"identity_{conv_id+1}"}
        for conv_id, (conv_raw, model, _) in enumerate(
            (conv_raw, model, _) for conv_raw in template_base for model in models_to_use for _ in range(repeats)
        )
    ]
    with open(f"{output_dir}/{template_needed}", "w") as template_dumped:
        json.dump(template, template_dumped, indent=2)
    return template

def run_tests(output_dir: str, template_id: str, template: List[Dict[str, Any]]) -> None:
    result: List[Dict[str, Any]] = []
    for conv_id in range(len(template)):
        model = template[conv_id]["model"]
        print(f"   - Identity {conv_id+1}/{len(template)} on {model}")
        messages: List[Dict[str, str]] = []
        for conv_message in template[conv_id]["conversations"]:
            messages.append({"content": conv_message["value"], "role": "user"})
            response = litellm.completion(model=model, messages=messages)
            messages.append({"content": response.choices[0].message.content, "role": "assistant"})
        result.append(copy.deepcopy(template[conv_id]))
        result[conv_id]["conversations"] = []
        for conv_message in messages:
            result[conv_id]["conversations"].append({
                "from": "human" if conv_message["role"] == "user" else "gpt",
                "value": conv_message["content"]
            })
    with open(f"{output_dir}/{template_id}", "w") as result_dumped:
        json.dump(result, result_dumped, indent=2)

if __name__ == '__main__':
    option: str = ''
    input_dir: str = r'atlas/data'
    output_dir: str = r'output'
    repeats: int = 5
    principles: List[int] = list(range(1, 27))
    categories: List[str] = ['boosting', 'correctness']
    models_to_use: List[str] = ['gpt4', 'gpt-3.5-turbo']
    if len(sys.argv) > 1:
        if '-p' in sys.argv:
            principles = []
        if '-c' in sys.argv:
            categories = []
        if '-m' in sys.argv:
            models_to_use = []
        for arg in range(1, len(sys.argv)):
            if sys.argv[arg][0] == "-":
                if sys.argv[arg] == '-h':
                    with open("help.txt", "r") as help_doc:
                        print(help_doc.read())
                    exit()
                else:
                    option = sys.argv[arg]
            else:
                match option:
                    case '-i':
                        input_dir = sys.argv[arg]
                    case '-o':
                        output_dir = sys.argv[arg]
                    case '-r':
                        repeats = int(sys.argv[arg])
                    case '-p':
                        principles.append(int(sys.argv[arg]))
                    case '-c':
                        categories.append(sys.argv[arg])
                    case '-m':
                        models_to_use.append(sys.argv[arg])
    print("Defining output structure...")
    template_ids = define_structure(input_dir, output_dir, principles, categories)
    templates: Dict[str, List[Dict[str, Any]]] = {}
    print("Creating templates...")
    for template_id in template_ids:
        templates[template_id] = create_template(input_dir, output_dir, models_to_use, template_id)
    print("Testing begins:")
    for template_id, template in templates.items():
        print(f" - {template_id}")
        run_tests(output_dir, template_id, template)
    print(f"Testing complete! Output is at {output_dir}")