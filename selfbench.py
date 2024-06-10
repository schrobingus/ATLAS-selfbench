import os, sys
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
    template_loaded = open(f"{input_dir}/{template_needed}", "r")
    template = json.loads(template_loaded.read())
    template_loaded.close()
    model_base = "gpt4"
    for conversation in reversed(range(len(template))):
        if template[conversation]["model"] != model_base:
            template.pop(conversation)
        else:
            for message in reversed(range(len(template[conversation]["conversations"]))):
                if template[conversation]["conversations"][message]["from"] == "gpt":
                    template[conversation]["conversations"].pop(message)
    template_to_save = open(f"{output_dir}/{template_needed}", "w")
    template_saved = json.dump(template, template_to_save, indent=2)
    template_to_save.close()

if __name__ == '__main__':
    option: str = ''
    input_dir: str = r'atlas/data'
    output_dir: str = r'output'
    principles: List[int] = list(range(1, 27))
    categories: List[str] = ['boosting', 'correctness']
    models_to_use: List[str] = ['ollama/gemma:2b', 'gpt4', 'ollama/phi3', 'gpt-3.5-turbo'] 
    # TODO: minimize `models_to_use` to gpt4 or so later on
    if len(sys.argv) > 1:
        if '-p' in sys.argv:
            principles = []
        if '-c' in sys.argv:
            categories = []
        for arg in range(1, len(sys.argv)):
            if sys.argv[arg][0] == "-":
                match sys.argv[arg]:
                    case '-h':
                        help_doc = open("help.txt", "r")
                        print(help_doc.read())
                        help_doc.close()
                        exit()
                    case _:
                        option = sys.argv[arg]
            else:
                match option:
                    case '-i':
                        input_dir = sys.argv[arg]
                    case '-o':
                        output_dir = sys.argv[arg]
                    case '-p':
                        principles.append(int(sys.argv[arg]))
                    case '-c':
                        categories.append(sys.argv[arg])
                    case '-h':
                        models_to_use.append(sys.argv[arg])
    template_ids = define_structure(input_dir, output_dir, principles, categories)
    for template in template_ids:
        create_template(input_dir, output_dir, models_to_use, template)