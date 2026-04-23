"""
Script để tải và chuẩn bị dataset HotpotQA cho Lab 16.
Yêu cầu: pip install requests tqdm
"""
from __future__ import annotations
import json
import random
from pathlib import Path

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("Cần cài đặt thư viện: pip install requests tqdm")
    exit(1)


def download_hotpotqa(num_samples: int = 120) -> list[dict]:
    """
    Tải HotpotQA dev set từ nguồn chính thức.
    Dataset gốc có ~7400 mẫu, ta lấy num_samples mẫu.
    """
    url = "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"
    
    print(f"Đang tải HotpotQA dev set từ {url}...")
    print("(File ~160MB, có thể mất vài phút)")
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Tải với progress bar
        total_size = int(response.headers.get('content-length', 0))
        data_bytes = b""
        
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                data_bytes += chunk
                pbar.update(len(chunk))
        
        data = json.loads(data_bytes.decode('utf-8'))
        print(f"Tải thành công! Tổng số mẫu trong dataset: {len(data)}")
        
        # Shuffle và lấy num_samples mẫu
        random.seed(42)  # Để reproducible
        sampled = random.sample(data, min(num_samples, len(data)))
        
        return sampled
        
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi tải: {e}")
        print("\nThử phương án backup: tải từ Hugging Face...")
        return download_from_huggingface(num_samples)


def download_from_huggingface(num_samples: int = 120) -> list[dict]:
    """
    Phương án backup: Tải từ Hugging Face datasets.
    """
    try:
        from datasets import load_dataset
        print("Đang tải từ Hugging Face...")
        ds = load_dataset("hotpot_qa", "distractor", split="validation")
        
        # Convert to list and sample
        data = list(ds)
        random.seed(42)
        sampled = random.sample(data, min(num_samples, len(data)))
        
        # Convert format
        converted = []
        for item in sampled:
            converted.append({
                "question": item["question"],
                "answer": item["answer"],
                "context": list(zip(item["context"]["title"], item["context"]["sentences"]))
            })
        return converted
        
    except ImportError:
        print("Để dùng Hugging Face, chạy: pip install datasets")
        return []


def assign_difficulty(question: str, answer: str) -> str:
    """
    Gán độ khó dựa trên đặc điểm câu hỏi.
    """
    q_lower = question.lower()
    
    # Hard: câu hỏi phức tạp, nhiều hop
    hard_keywords = ["how many", "which", "what year", "when did", "comparison"]
    if any(kw in q_lower for kw in hard_keywords) and len(question) > 80:
        return "hard"
    
    # Easy: câu hỏi ngắn, answer ngắn
    if len(question) < 50 and len(answer.split()) <= 3:
        return "easy"
    
    return "medium"


def convert_to_lab_format(raw_data: list[dict], start_id: int = 1) -> list[dict]:
    """
    Chuyển đổi dữ liệu HotpotQA sang format của Lab.
    """
    converted = []
    
    for i, item in enumerate(tqdm(raw_data, desc="Converting")):
        qid = f"hq{start_id + i}"
        question = item.get("question", "")
        answer = item.get("answer", "")
        
        # Xử lý context - HotpotQA có format đặc biệt
        context_list = []
        raw_context = item.get("context", [])
        
        for ctx in raw_context:
            if isinstance(ctx, (list, tuple)) and len(ctx) >= 2:
                title = ctx[0]
                sentences = ctx[1]
                # Sentences có thể là list hoặc string
                if isinstance(sentences, list):
                    text = " ".join(sentences)
                else:
                    text = str(sentences)
                context_list.append({
                    "title": title,
                    "text": text
                })
        
        # Chỉ lấy tối đa 4 context passages để giảm token
        context_list = context_list[:4]
        
        # Bỏ qua nếu thiếu dữ liệu quan trọng
        if not question or not answer or not context_list:
            continue
        
        converted.append({
            "qid": qid,
            "difficulty": assign_difficulty(question, answer),
            "question": question,
            "gold_answer": answer,
            "context": context_list
        })
    
    return converted


def save_dataset(data: list[dict], output_path: str) -> None:
    """Lưu dataset ra file JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Đã lưu {len(data)} mẫu vào {output_path}")


def show_statistics(data: list[dict]) -> None:
    """Hiển thị thống kê dataset."""
    print("\n" + "="*50)
    print("THỐNG KÊ DATASET")
    print("="*50)
    
    total = len(data)
    difficulties = {"easy": 0, "medium": 0, "hard": 0}
    
    for item in data:
        diff = item.get("difficulty", "medium")
        difficulties[diff] = difficulties.get(diff, 0) + 1
    
    print(f"Tổng số mẫu: {total}")
    print(f"  - Easy:   {difficulties['easy']} ({100*difficulties['easy']/total:.1f}%)")
    print(f"  - Medium: {difficulties['medium']} ({100*difficulties['medium']/total:.1f}%)")
    print(f"  - Hard:   {difficulties['hard']} ({100*difficulties['hard']/total:.1f}%)")
    
    # Sample questions
    print("\nVí dụ một số câu hỏi:")
    for i, item in enumerate(data[:3]):
        print(f"\n{i+1}. [{item['difficulty']}] {item['question']}")
        print(f"   Answer: {item['gold_answer']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Tải và chuẩn bị HotpotQA dataset")
    parser.add_argument("--num-samples", type=int, default=120, 
                        help="Số lượng mẫu cần tải (mặc định: 120)")
    parser.add_argument("--output", type=str, default="data/hotpot_100.json",
                        help="Đường dẫn file output (mặc định: data/hotpot_100.json)")
    
    args = parser.parse_args()
    
    print("="*50)
    print("CHUẨN BỊ DATASET HOTPOTQA CHO LAB 16")
    print("="*50)
    
    # Bước 1: Tải dữ liệu
    raw_data = download_hotpotqa(args.num_samples)
    
    if not raw_data:
        print("Không thể tải dữ liệu. Vui lòng kiểm tra kết nối mạng.")
        return
    
    # Bước 2: Chuyển đổi format
    print(f"\nĐang chuyển đổi {len(raw_data)} mẫu sang format của Lab...")
    converted = convert_to_lab_format(raw_data)
    
    # Bước 3: Lưu file
    save_dataset(converted, args.output)
    
    # Bước 4: Hiển thị thống kê
    show_statistics(converted)
    
    print("\n" + "="*50)
    print("HOÀN TẤT!")
    print("="*50)
    print(f"\nBạn có thể chạy benchmark với dataset mới:")
    print(f"  python run_benchmark.py --dataset {args.output} --out-dir outputs/real_run")


if __name__ == "__main__":
    main()
