"""
Tạo bộ dataset mini cân bằng: 10 easy + 10 medium + 10 hard = 30 mẫu
"""
import json
import random
from pathlib import Path

def create_balanced_mini(input_path: str, output_path: str):
    # Đọc dataset gốc
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Phân loại theo difficulty
    easy = [item for item in data if item.get("difficulty") == "easy"]
    medium = [item for item in data if item.get("difficulty") == "medium"]
    hard = [item for item in data if item.get("difficulty") == "hard"]
    
    print(f"Original dataset: {len(data)} samples")
    print(f"  - Easy: {len(easy)}")
    print(f"  - Medium: {len(medium)}")
    print(f"  - Hard: {len(hard)}")
    
    # Random chọn mẫu - đảm bảo đủ 30 mẫu
    random.seed(42)
    
    # Lấy tất cả easy (chỉ có 2)
    selected_easy = easy[:] 
    # Lấy 10 hard
    selected_hard = random.sample(hard, min(10, len(hard)))
    # Lấy medium để đủ 30 mẫu (30 - 2 - 10 = 18)
    num_medium_needed = 30 - len(selected_easy) - len(selected_hard)
    selected_medium = random.sample(medium, min(num_medium_needed, len(medium)))
    
    # Gộp lại và đánh số lại qid
    mini_dataset = []
    
    for i, item in enumerate(selected_easy):
        item["qid"] = f"easy_{i+1}"
        mini_dataset.append(item)
    
    for i, item in enumerate(selected_medium):
        item["qid"] = f"med_{i+1}"
        mini_dataset.append(item)
    
    for i, item in enumerate(selected_hard):
        item["qid"] = f"hard_{i+1}"
        mini_dataset.append(item)
    
    # Shuffle để trộn đều
    random.shuffle(mini_dataset)
    
    # Lưu file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mini_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\nCreated: {output_path}")
    print(f"Total: {len(mini_dataset)} samples ({len(selected_easy)} easy + {len(selected_medium)} medium + {len(selected_hard)} hard)")
    
    print("\nSample questions:")
    for item in mini_dataset[:5]:
        print(f"  [{item['difficulty']}] {item['question'][:60]}...")

if __name__ == "__main__":
    create_balanced_mini(
        input_path="data/hotpot_100.json",
        output_path="data/hotpot_mini_30.json"
    )
