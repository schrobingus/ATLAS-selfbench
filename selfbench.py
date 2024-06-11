import os, sys
import copy
from typing import Any, Dict, List
import json

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

def create_template(input_dir: str, output_dir: str, models_to_use: List[str], template_needed: str) -> None:
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

if __name__ == '__main__':
    option: str = ''
    input_dir: str = r'atlas/data'
    output_dir: str = r'output'
    repeats: int = 5
    principles: List[int] = list(range(1, 27))
    categories: List[str] = ['boosting', 'correctness']
    models_to_use: List[str] = ['ollama/gemma:2b', 'gpt4', 'ollama/phi3', 'gpt-3.5-turbo']
    if len(sys.argv) > 1:
        if '-p' in sys.argv:
            principles = []
        if '-c' in sys.argv:
            categories = []
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
    template_ids = define_structure(input_dir, output_dir, principles, categories)
    for template in template_ids:
        create_template(input_dir, output_dir, models_to_use, template)