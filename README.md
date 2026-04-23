# Lab 16 — Reflexion Agent Scaffold

Repo này cung cấp một khung sườn (scaffold) để xây dựng và đánh giá **Reflexion Agent**.

## 1. Mục tiêu của Repo
- Repo hiện tại đã được triển khai với **LLM thật** (OpenAI GPT-3.5-turbo) thông qua `llm_runtime.py`.
- Mục đích giúp học viên hiểu rõ về **flow**, các bước **loop**, cách thức hoạt động của cơ chế phản chiếu (reflection) và cách đánh giá (evaluation).

## 2. Nhiệm vụ đã hoàn thành
| Nhiệm vụ | Trạng thái | Mô tả |
|----------|------------|-------|
| Xây dựng Agent thật | ✅ | Sử dụng OpenAI GPT-3.5-turbo trong `llm_runtime.py` |
| Chạy Benchmark 100+ mẫu | ✅ | Dataset `hotpot_100.json` với 120 mẫu từ HotpotQA |
| Định dạng báo cáo | ✅ | Xuất `report.json` và `report.md` đúng format |
| Tính toán Token thực tế | ✅ | Lấy từ `response.usage.total_tokens` của OpenAI API |

## 3. Cách chạy Lab

### 3.1. Cài đặt môi trường
```bash
# Tạo virtual environment
python -m venv .venv

# Kích hoạt (Windows PowerShell)
.\.venv\Scripts\Activate

# Kích hoạt (Linux/Mac)
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3.2. Cấu hình API Key
Tạo file `.env` trong thư mục gốc:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3.3. Chạy Benchmark
```bash
# Chạy với dataset nhỏ (8 mẫu) để test
python run_benchmark.py --dataset data/hotpot_mini.json --out-dir outputs/test_run

# Chạy với dataset đầy đủ (120 mẫu)
python run_benchmark.py --dataset data/hotpot_100.json --out-dir outputs/real_run

# Chạy chấm điểm tự động
python autograde.py --report-path outputs/real_run/report.json
```

## 4. Tiêu chí chấm điểm (Rubric)

### 4.1. Core Flow (80 điểm)
| Tiêu chí | Điểm | Mô tả |
|----------|------|-------|
| Schema completeness | 30 | Có đủ các keys: meta, summary, failure_modes, examples, extensions, discussion |
| Experiment completeness | 30 | Có cả react + reflexion, >= 100 records, >= 20 examples |
| Analysis depth | 20 | failure_modes >= 3 keys, discussion >= 250 ký tự |

### 4.2. Bonus Features (20 điểm)
| Feature | Điểm | Trạng thái | Mô tả |
|---------|------|------------|-------|
| `structured_evaluator` | 10 | ✅ | Evaluator trả về JSON có cấu trúc (score, reason, missing_evidence, spurious_claims) |
| `reflection_memory` | 10 | ✅ | Lưu trữ bài học giữa các attempts để Actor cải thiện |
| `adaptive_max_attempts` | 10 | ✅ | Tự động điều chỉnh số lần thử theo độ khó (easy: 2, medium: 3, hard: 4) |
| `memory_compression` | 10 | ✅ | Nén reflection memory xuống còn 3 items khi quá dài |
| `benchmark_report_json` | 10 | ✅ | Xuất báo cáo dạng JSON |

**Lưu ý**: Tối đa 20 điểm bonus (cần ít nhất 2 features).

## 5. Thành phần mã nguồn

| File | Mô tả |
|------|-------|
| `src/reflexion_lab/schemas.py` | Định nghĩa các kiểu dữ liệu: `JudgeResult`, `ReflectionEntry`, `AttemptTrace`, `RunRecord` |
| `src/reflexion_lab/prompts.py` | System prompts cho Actor, Evaluator và Reflector (tiếng Việt) |
| `src/reflexion_lab/llm_runtime.py` | **MỚI** - Logic gọi OpenAI API thật |
| `src/reflexion_lab/agents.py` | ReAct và Reflexion Agent với bonus features |
| `src/reflexion_lab/reporting.py` | Logic xuất báo cáo benchmark |
| `run_benchmark.py` | Script chính để chạy đánh giá (có progress bar) |
| `autograde.py` | Công cụ chấm điểm tự động |

## 6. Chi tiết Bonus Features đã implement

### 6.1. Adaptive Max Attempts
```python
def get_adaptive_max_attempts(difficulty: str, base_attempts: int = 3) -> int:
    difficulty_multiplier = {
        "easy": 0.67,    # 2 attempts
        "medium": 1.0,   # 3 attempts  
        "hard": 1.33     # 4 attempts
    }
    return max(1, round(base_attempts * multiplier))
```

### 6.2. Memory Compression
```python
def compress_memory(memory: list[str], max_items: int = 3) -> list[str]:
    if len(memory) <= max_items:
        return memory
    return memory[-max_items:]  # Giữ lại các bài học gần nhất
```

### 6.3. Structured Evaluator
Evaluator trả về JSON với cấu trúc:
```json
{
    "score": 0 hoặc 1,
    "reason": "giải thích ngắn gọn",
    "missing_evidence": ["thông tin còn thiếu"],
    "spurious_claims": ["thông tin sai"]
}
```

### 6.4. Failure Mode Detection
Tự động phát hiện loại lỗi:
- `entity_drift`: Agent bị lạc sang entity khác
- `incomplete_multi_hop`: Dừng lại ở bước 1
- `wrong_final_answer`: Suy luận đúng nhưng chọn sai
- `looping`: Câu trả lời lặp lại câu hỏi

## 7. Datasets

| File | Số mẫu | Mô tả |
|------|--------|-------|
| `data/hotpot_mini.json` | 8 | Dataset gốc để test nhanh |
| `data/hotpot_100.json` | 120 | Dataset chính từ HotpotQA |
| `data/hotpot_mini_22.json` | 22 | Dataset cân bằng (2 easy + 10 medium + 10 hard) |

## 8. Kết quả mẫu

Sau khi chạy `python autograde.py --report-path outputs/real_run/report.json`:

```
Auto-grade total: 100/100
- Flow Score (Core): 80/80
  * Schema: 30/30
  * Experiment: 30/30
  * Analysis: 20/20
- Bonus Score: 20/20
```
