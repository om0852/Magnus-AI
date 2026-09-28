import time
import statistics
import json
import os
from typing import List, Dict, Any
from nlp.inference.engine import InferenceEngine
from nlp.training.dataset_generator import generate_dataset

def run_benchmark(num_test_samples: int = 1000) -> Dict[str, Any]:
    print(f"==================================================")
    print(f" MAGNAS NLP BENCHMARK & EVALUATION SUITE")
    print(f" Evaluating {num_test_samples} unseen test samples...")
    print(f"==================================================")

    # Initialize inference engine
    start_init = time.time()
    engine = InferenceEngine()
    init_time_ms = (time.time() - start_init) * 1000

    # Generate held-out evaluation dataset
    test_data = generate_dataset(num_test_samples)

    intent_correct = 0
    unknown_total = 0
    unknown_correct = 0
    false_actions = 0
    latencies = []

    for item in test_data:
        text = item["text"]
        target_intent = item["intent"]

        t0 = time.perf_counter()
        pred = engine.parse(text)
        t1 = time.perf_counter()
        
        latency_ms = (t1 - t0) * 1000
        latencies.append(latency_ms)

        pred_intent = pred.get("intent")

        if pred_intent == target_intent:
            intent_correct += 1

        if target_intent == "UNKNOWN":
            unknown_total += 1
            if pred_intent == "UNKNOWN":
                unknown_correct += 1
            else:
                false_actions += 1

    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    p99_latency = max(latencies)
    throughput_qps = 1000.0 / avg_latency if avg_latency > 0 else 0

    intent_accuracy = (intent_correct / len(test_data)) * 100
    unknown_detection_rate = (unknown_correct / unknown_total * 100) if unknown_total > 0 else 100.0
    false_action_rate = (false_actions / len(test_data)) * 100

    results = {
        "num_samples": num_test_samples,
        "engine_init_ms": round(init_time_ms, 2),
        "intent_accuracy_percent": round(intent_accuracy, 2),
        "unknown_detection_rate_percent": round(unknown_detection_rate, 2),
        "false_action_rate_percent": round(false_action_rate, 2),
        "avg_latency_ms": round(avg_latency, 4),
        "p95_latency_ms": round(p95_latency, 4),
        "p99_latency_ms": round(p99_latency, 4),
        "throughput_queries_per_sec": round(throughput_qps, 2)
    }

    print("\n--- BENCHMARK RESULTS ---")
    print(f" Intent Classification Accuracy: {results['intent_accuracy_percent']}%")
    print(f" Unknown/Safe Detection Rate   : {results['unknown_detection_rate_percent']}%")
    print(f" False Action Rate             : {results['false_action_rate_percent']}%")
    print(f" Average Latency per Query     : {results['avg_latency_ms']} ms")
    print(f" 95th Percentile Latency (p95) : {results['p95_latency_ms']} ms")
    print(f" Local CPU Throughput          : {results['throughput_queries_per_sec']} queries/sec")
    print("==================================================")

    return results

if __name__ == "__main__":
    run_benchmark(1000)
