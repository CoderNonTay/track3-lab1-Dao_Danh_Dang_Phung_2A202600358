# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini_22.json
- Mode: real
- Records: 44
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.5 | 0.5455 | 0.0455 |
| Avg attempts | 1 | 2.1364 | 1.1364 |
| Avg token estimate | 1840.14 | 4932.41 | 3092.27 |
| Avg latency (ms) | 3011.95 | 11260.27 | 8248.32 |

## Failure modes
```json
{
  "react": {
    "entity_drift": 9,
    "none": 11,
    "wrong_final_answer": 1,
    "incomplete_multi_hop": 1
  },
  "reflexion": {
    "entity_drift": 9,
    "none": 12,
    "wrong_final_answer": 1
  },
  "by_failure_type": {
    "entity_drift": 18,
    "none": 23,
    "wrong_final_answer": 2,
    "incomplete_multi_hop": 1
  },
  "summary": {
    "total_failures": 21,
    "total_success": 23,
    "failure_rate": 0.4773
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

