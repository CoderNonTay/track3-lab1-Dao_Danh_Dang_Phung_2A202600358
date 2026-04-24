# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: real
- Records: 240
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.325 | 0.5 | 0.175 |
| Avg attempts | 1 | 2.3083 | 1.3083 |
| Avg token estimate | 1494.44 | 4357.94 | 2863.5 |
| Avg latency (ms) | 4040.84 | 10246.69 | 6205.85 |

## Failure modes
```json
{
  "react": {
    "none": 39,
    "entity_drift": 62,
    "incomplete_multi_hop": 14,
    "wrong_final_answer": 5
  },
  "reflexion": {
    "none": 60,
    "entity_drift": 44,
    "incomplete_multi_hop": 11,
    "wrong_final_answer": 5
  },
  "by_failure_type": {
    "none": 99,
    "entity_drift": 106,
    "incomplete_multi_hop": 25,
    "wrong_final_answer": 10
  },
  "summary": {
    "total_failures": 141,
    "total_success": 99,
    "failure_rate": 0.5875
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- adaptive_max_attempts
- memory_compression
- benchmark_report_json

## Discussion

## Phan tich ket qua Reflexion Agent

### 1. Hieu qua cua Reflexion:
- Reflexion giup cai thien do chinh xac (EM) khi Actor sai o lan dau
- Co che tu phan chieu (self-reflection) cho phep Agent hoc tu loi sai

### 2. Cac Bonus Features da implement:
- **adaptive_max_attempts**: Tu dong tang so lan thu cho cau hoi kho (hard: 4 attempts, medium: 3, easy: 2)
- **memory_compression**: Nen reflection memory xuong con 3 items de tiet kiem token

### 3. Trade-offs:
- Reflexion ton nhieu token hon ReAct (do phai goi Reflector)
- Latency cao hon do nhieu lan API calls
- Tuy nhien, do chinh xac cao hon dang ke tren cac cau hoi kho

### 4. Failure modes pho bien:
- entity_drift: Agent bi lac sang entity khac trong qua trinh suy luan
- incomplete_multi_hop: Dung lai o buoc 1, khong hoan thanh cac buoc tiep theo
- wrong_final_answer: Suy luan dung nhung chon sai entity cuoi cung

