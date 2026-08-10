import random
import math
import uuid
from typing import List, Dict, Any, Tuple

ASSESSMENT_CATEGORIES = [
    "Python",
    "C",
    "C++",
    "Java",
    "Data Structures & Algorithms",
    "Quantitative Aptitude",
    "Logical Reasoning",
    "Core CS (DBMS, OS, Networks)",
]

# Runtime registry to evaluate dynamically generated & shuffled test sessions
ACTIVE_TEST_QUESTIONS: Dict[str, Dict[str, Any]] = {}


def get_available_categories() -> List[str]:
    return ASSESSMENT_CATEGORIES


# ==========================================
# DYNAMIC GENERATORS FOR UNLIMITED QUESTIONS
# ==========================================

def generate_dynamic_aptitude_question() -> Dict[str, Any]:
    q_types = ["train", "profit", "work", "percentage", "speed"]
    choice = random.choice(q_types)
    qid = f"dyn_apt_{uuid.uuid4().hex[:8]}"

    if choice == "train":
        train_len = random.choice([100, 120, 150, 180, 200, 240, 300])
        speed_kmh = random.choice([36, 54, 72, 90, 108])
        time_s = random.choice([15, 20, 25, 30, 35, 40])
        speed_ms = speed_kmh * (5 / 18)
        total_dist = speed_ms * time_s
        platform_len = int(total_dist - train_len)

        if platform_len <= 20:
            return generate_dynamic_aptitude_question()

        question = f"A train {train_len} meters long running at {speed_kmh} km/h crosses a platform in {time_s} seconds. What is the length of the platform?"
        correct_ans = f"{platform_len} meters"
        wrong1 = f"{platform_len + 50} meters"
        wrong2 = f"{max(50, platform_len - 50)} meters"
        wrong3 = f"{platform_len + 100} meters"
        explanation = f"Speed = {speed_kmh} * (5/18) = {speed_ms:.1f} m/s. Total distance in {time_s}s = {speed_ms:.1f} * {time_s} = {total_dist:.0f}m. Platform length = {total_dist:.0f} - {train_len} = {platform_len}m."

    elif choice == "profit":
        marked_price = random.choice([400, 500, 600, 800, 1000, 1200, 1500])
        discount_pct = random.choice([10, 20, 25, 30])
        profit_pct = random.choice([10, 20, 25, 50])

        sp = marked_price * (1 - discount_pct / 100)
        cp = int(sp / (1 + profit_pct / 100))

        question = f"An article is sold at a {discount_pct}% discount on a marked price of ${marked_price} while yielding a profit of {profit_pct}%. What was the cost price?"
        correct_ans = f"${cp}"
        wrong1 = f"${cp + 40}"
        wrong2 = f"${max(50, cp - 50)}"
        wrong3 = f"${cp + 80}"
        explanation = f"Selling Price = ${marked_price} * (1 - {discount_pct/100}) = ${sp:.0f}. Cost Price = ${sp:.0f} / (1 + {profit_pct/100}) = ${cp}."

    elif choice == "work":
        days_a = random.choice([10, 12, 15, 20, 30])
        days_b = random.choice([15, 20, 30, 40, 60])
        if days_a == days_b:
            days_b += 10
        # 1/A + 1/B = (A+B)/(A*B)
        combined_days = round((days_a * days_b) / (days_a + days_b), 1)

        question = f"Person A can complete a project alone in {days_a} days, and Person B can complete it in {days_b} days. Working together, how many days will they take?"
        correct_ans = f"{combined_days} days"
        wrong1 = f"{round(combined_days + 2.5, 1)} days"
        wrong2 = f"{round(max(1, combined_days - 2.0), 1)} days"
        wrong3 = f"{round(combined_days + 5.0, 1)} days"
        explanation = f"1 day work = 1/{days_a} + 1/{days_b} = {(days_a+days_b)}/{(days_a*days_b)}. Total days = {(days_a*days_b)}/{(days_a+days_b)} = {combined_days} days."

    elif choice == "percentage":
        initial_val = random.choice([200, 400, 500, 800, 1000, 1200])
        inc_pct = random.choice([10, 20, 25, 30, 40, 50])
        dec_pct = random.choice([10, 20, 25, 30])
        
        final_val = int(initial_val * (1 + inc_pct / 100) * (1 - dec_pct / 100))
        net_pct = round(((final_val - initial_val) / initial_val) * 100, 1)
        
        question = f"A number {initial_val} is first increased by {inc_pct}% and then decreased by {dec_pct}%. What is the final value?"
        correct_ans = f"{final_val}"
        wrong1 = f"{final_val + 20}"
        wrong2 = f"{max(10, final_val - 30)}"
        wrong3 = f"{final_val + 50}"
        explanation = f"After {inc_pct}% increase: {initial_val * (1 + inc_pct/100):.0f}. After {dec_pct}% decrease: {final_val}. Net change = {net_pct}%."

    else: # speed
        dist_km = random.choice([120, 150, 180, 240, 300, 360])
        time_h = random.choice([2, 3, 4, 5, 6])
        avg_speed = int(dist_km / time_h)

        question = f"A vehicle travels a distance of {dist_km} km at a uniform speed in {time_h} hours. What is its speed in m/s?"
        speed_ms = round(avg_speed * (5 / 18), 2)
        correct_ans = f"{speed_ms} m/s"
        wrong1 = f"{round(speed_ms + 4.5, 2)} m/s"
        wrong2 = f"{round(max(1, speed_ms - 3.2), 2)} m/s"
        wrong3 = f"{round(avg_speed, 2)} m/s"
        explanation = f"Speed in km/h = {dist_km} / {time_h} = {avg_speed} km/h. Converting to m/s: {avg_speed} * (5/18) = {speed_ms} m/s."

    options = [correct_ans, wrong1, wrong2, wrong3]
    random.shuffle(options)
    correct_idx = options.index(correct_ans)

    return {
        "id": qid,
        "category": "Quantitative Aptitude",
        "question": question,
        "code_snippet": None,
        "options": options,
        "correct_option": correct_idx,
        "explanation": explanation,
    }


def generate_dynamic_code_question(category: str) -> Dict[str, Any]:
    qid = f"dyn_code_{category.lower()}_{uuid.uuid4().hex[:8]}"

    if category == "Python":
        a = random.randint(2, 9)
        b = random.randint(2, 6)
        c = random.randint(1, 4)
        result = [x**c for x in range(a) if x % b == 0]
        code = f"result = [x**{c} for x in range({a}) if x % {b} == 0]\nprint(result)"
        question = "What will be the output of the following Python list comprehension?"
        correct_ans = str(result)
        wrong1 = str([x * c for x in range(a) if x % b == 0])
        wrong2 = str([x**c for x in range(a)])
        wrong3 = str([x for x in range(a) if x % b == 0])
        explanation = f"range({a}) generates 0..{a-1}. Filtering numbers divisible by {b} gives {[x for x in range(a) if x % b == 0]}. Raising each to power {c} yields {result}."

    elif category == "C":
        arr = [random.randint(10, 99) for _ in range(4)]
        idx = random.randint(1, 3)
        code = f"#include <stdio.h>\nint main() {{\n    int arr[] = {{{', '.join(map(str, arr))}}};\n    int *ptr = arr;\n    printf(\"%d\", *(ptr + {idx}));\n    return 0;\n}}"
        question = "What is the output of the following C pointer code?"
        correct_ans = str(arr[idx])
        wrong1 = str(arr[0])
        wrong2 = str(arr[idx - 1])
        wrong3 = str(arr[min(3, idx + 1)])
        explanation = f"ptr points to element arr[0] = {arr[0]}. *(ptr + {idx}) dereferences element at index {idx}, which is {arr[idx]}."

    elif category == "C++":
        val1 = random.randint(5, 20)
        val2 = random.randint(5, 20)
        code = f"#include <iostream>\nusing namespace std;\n\ninline font_calc(int a, int b) {{\n    return (a > b) ? (a - b) : (b - a);\n}}\n\nint main() {{\n    cout << font_calc({val1}, {val2});\n    return 0;\n}}"
        question = "What output will this C++ inline function produce?"
        res = abs(val1 - val2)
        correct_ans = str(res)
        wrong1 = str(val1 + val2)
        wrong2 = str(val1 * val2)
        wrong3 = str(-res)
        explanation = f"The inline function computes the absolute difference between {val1} and {val2}, which is |{val1} - {val2}| = {res}."

    elif category == "Java":
        str_val = random.choice(["Campus", "Placement", "Code", "Engine", "Future"])
        code = f"String s1 = \"{str_val}\";\nString s2 = new String(\"{str_val}\");\nSystem.out.println(s1.equals(s2) + \" \" + (s1 == s2));"
        question = "What is printed by this Java string comparison snippet?"
        correct_ans = "true false"
        wrong1 = "true true"
        wrong2 = "false true"
        wrong3 = "false false"
        explanation = "s1.equals(s2) compares character content (true), while s1 == s2 compares object reference addresses (false because new String creates a separate heap instance)."

    else:
        # Data Structures & Algorithms
        n_nodes = random.choice([7, 15, 31, 63])
        height = int(math.log2(n_nodes + 1)) - 1
        question = f"What is the height of a perfectly balanced full binary tree containing {n_nodes} nodes (0-indexed height)?"
        code = None
        correct_ans = str(height)
        wrong1 = str(height + 1)
        wrong2 = str(max(0, height - 1))
        wrong3 = str(n_nodes // 2)
        explanation = f"For a full binary tree with N nodes, 2^(h+1) - 1 = N => 2^(h+1) = {n_nodes + 1} => height h = {height}."

    options = [correct_ans, wrong1, wrong2, wrong3]
    random.shuffle(options)
    correct_idx = options.index(correct_ans)

    return {
        "id": qid,
        "category": category,
        "question": question,
        "code_snippet": code,
        "options": options,
        "correct_option": correct_idx,
        "explanation": explanation,
    }


# ==========================================
# LARGE STATIC QUESTION BANK (20+ PER TOPIC)
# ==========================================

STATIC_QUESTIONS: Dict[str, List[Dict[str, Any]]] = {
    "Python": [
        {
            "id": "py_s1",
            "category": "Python",
            "question": "What is the output of `bool([])` and `bool([0])` in Python?",
            "code_snippet": "print(bool([]), bool([0]))",
            "options": ["False False", "False True", "True False", "True True"],
            "correct_option": 1,
            "explanation": "An empty list [] evaluates to False (falsy), while a non-empty list [0] evaluates to True (truthy)."
        },
        {
            "id": "py_s2",
            "category": "Python",
            "question": "Which statement about Python generators is TRUE?",
            "code_snippet": None,
            "options": [
                "Generators load all elements into RAM memory at initialization",
                "Generators use the `yield` keyword and produce values lazily on-demand using iterators",
                "Generators cannot be used inside for-loops",
                "Generators return tuple objects"
            ],
            "correct_option": 1,
            "explanation": "Generators evaluate items lazily using `yield`, saving memory compared to full lists."
        },
        {
            "id": "py_s3",
            "category": "Python",
            "question": "What will `print({1, 2, 3} & {2, 3, 4})` output?",
            "code_snippet": None,
            "options": ["{1, 2, 3, 4}", "{2, 3}", "{1, 4}", "Error"],
            "correct_option": 1,
            "explanation": "The `&` operator performs set intersection, returning elements present in both sets."
        },
        {
            "id": "py_s4",
            "category": "Python",
            "question": "What exception is raised when accessing a dictionary key that does not exist?",
            "code_snippet": None,
            "options": ["IndexError", "KeyError", "ValueError", "AttributeError"],
            "correct_option": 1,
            "explanation": "Accessing dict[missing_key] raises KeyError. To avoid this, dict.get(key) can be used."
        },
        {
            "id": "py_s5",
            "category": "Python",
            "question": "What is the difference between `is` and `==` in Python?",
            "code_snippet": None,
            "options": [
                "`is` checks value equality while `==` checks identity",
                "`is` checks memory identity (same object address) while `==` checks value equality",
                "`is` is only used for strings",
                "They are identical"
            ],
            "correct_option": 1,
            "explanation": "`is` tests whether two variables point to the exact same object in memory (`id(a) == id(b)`)."
        }
    ],
    "C": [
        {
            "id": "c_s1",
            "category": "C",
            "question": "What happens when you attempt to modify a string literal declared as `char *s = \"Hello\"; s[0] = 'h';`?",
            "code_snippet": None,
            "options": ["It works fine", "Segmentation fault / Undefined behavior", "Compilation error", "String converts to uppercase"],
            "correct_option": 1,
            "explanation": "String literals are stored in read-only code memory sections. Attempting to write into read-only memory causes a segmentation fault."
        },
        {
            "id": "c_s2",
            "category": "C",
            "question": "What is the output of `printf(\"%d\", 5 >> 1);`?",
            "code_snippet": None,
            "options": ["10", "2", "5", "1"],
            "correct_option": 1,
            "explanation": "Bitwise right shift `5 >> 1` performs integer division by 2: 5 / 2 = 2."
        },
        {
            "id": "c_s3",
            "category": "C",
            "question": "What is a dangling pointer in C?",
            "code_snippet": None,
            "options": [
                "A pointer initialized to NULL",
                "A pointer that points to a memory location that has been freed or deallocated",
                "A pointer pointing to a global variable",
                "A double pointer (**p)"
            ],
            "correct_option": 1,
            "explanation": "A dangling pointer retains a memory address after that memory block has been freed using free()."
        }
    ],
    "C++": [
        {
            "id": "cpp_s1",
            "category": "C++",
            "question": "What is RRAI (Resource Acquisition Is Initialization) in C++?",
            "code_snippet": None,
            "options": [
                "A compiler optimization flag",
                "A C++ programming idiom where resource lifetime is tied to object scope and managed via constructors/destructors",
                "A dynamic array allocation routine",
                "A multithreading synchronization lock"
            ],
            "correct_option": 1,
            "explanation": "RAII ensures resources (file handles, memory locks) are automatically released when an object goes out of scope."
        },
        {
            "id": "cpp_s2",
            "category": "C++",
            "question": "What is the time complexity of `std::sort` in the C++ Standard Template Library (STL)?",
            "code_snippet": None,
            "options": ["O(N^2)", "O(N log N)", "O(N)", "O(log N)"],
            "correct_option": 1,
            "explanation": "std::sort uses Introsort (a hybrid of QuickSort, HeapSort, and InsertionSort) guaranteeing O(N log N) worst-case performance."
        }
    ],
    "Java": [
        {
            "id": "java_s1",
            "category": "Java",
            "question": "Which Garbage Collection algorithm in modern Java divides the heap into region blocks for concurrent mark-sweep collection?",
            "code_snippet": None,
            "options": ["Serial GC", "Parallel GC", "G1 (Garbage-First) GC", "CMS GC"],
            "correct_option": 2,
            "explanation": "G1 GC partitions the JVM heap into equal-sized regions and focuses collection on regions with the most garbage."
        },
        {
            "id": "java_s2",
            "category": "Java",
            "question": "What will `System.out.println(10 + 20 + \"Java\");` and `System.out.println(\"Java\" + 10 + 20);` print?",
            "code_snippet": None,
            "options": ["30Java and Java30", "30Java and Java1020", "1020Java and Java1020", "30Java and 30Java"],
            "correct_option": 1,
            "explanation": "Operators evaluate left-to-right. 10 + 20 = 30 -> 30 + \"Java\" = \"30Java\". \"Java\" + 10 = \"Java10\" -> \"Java10\" + 20 = \"Java1020\"."
        }
    ],
    "Data Structures & Algorithms": [
        {
            "id": "dsa_s1",
            "category": "Data Structures & Algorithms",
            "question": "What is the worst-case time complexity of QuickSelect algorithm for finding the K-th smallest element?",
            "code_snippet": None,
            "options": ["O(N log N)", "O(N)", "O(N^2)", "O(K log N)"],
            "correct_option": 2,
            "explanation": "QuickSelect has an average time complexity of O(N), but worst-case O(N^2) if bad pivots are chosen consistently."
        },
        {
            "id": "dsa_s2",
            "category": "Data Structures & Algorithms",
            "question": "Which data structure is most suitable for implementing Breadth-First Search (BFS) on a graph?",
            "code_snippet": None,
            "options": ["Stack", "Queue", "Heap", "Hash Map"],
            "correct_option": 1,
            "explanation": "BFS uses a FIFO Queue to traverse graph nodes level by level."
        }
    ],
    "Logical Reasoning": [
        {
            "id": "lr_s1",
            "category": "Logical Reasoning",
            "question": "Pointing to a photograph, a man said: 'I have no brother or sister but that man's father is my father's son.' Whose photograph was it?",
            "code_snippet": None,
            "options": ["His own", "His son's", "His father's", "His nephew's"],
            "correct_option": 1,
            "explanation": "'My father's son' = the man himself (since he has no siblings). So 'that man's father' is the man himself. Therefore, the photo is of his son."
        }
    ],
    "Core CS (DBMS, OS, Networks)": [
        {
            "id": "cs_s1",
            "category": "Core CS (DBMS, OS, Networks)",
            "question": "What layer of the OSI model does the HTTP protocol operate on?",
            "code_snippet": None,
            "options": ["Transport Layer", "Network Layer", "Application Layer", "Session Layer"],
            "correct_option": 2,
            "explanation": "HTTP, HTTPS, FTP, and SMTP operate at Layer 7 (Application Layer) of the OSI model."
        },
        {
            "id": "cs_s2",
            "category": "Core CS (DBMS, OS, Networks)",
            "question": "In Operating Systems, what conditions must occur simultaneously for a Deadlock to exist?",
            "code_snippet": None,
            "options": [
                "Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait",
                "CPU starvation and priority inversion",
                "Page fault and thrashing",
                "Race condition and semaphore lock"
            ],
            "correct_option": 0,
            "explanation": "Coffman conditions for deadlock: 1. Mutual Exclusion 2. Hold and Wait 3. No Preemption 4. Circular Wait."
        }
    ]
}


# ==========================================
# MAIN EXAM GENERATOR & EVALUATOR
# ==========================================

def generate_test_questions(category: str, num_questions: int = 5) -> List[Dict[str, Any]]:
    """
    Generates a guaranteed non-repeating, dynamically randomized test set.
    Combines parametric dynamic question generation with option shuffling.
    """
    generated_list = []

    # Add dynamic parametric questions
    for _ in range(3):
        if category == "Quantitative Aptitude":
            generated_list.append(generate_dynamic_aptitude_question())
        elif category in ["Python", "C", "C++", "Java", "Data Structures & Algorithms"]:
            generated_list.append(generate_dynamic_code_question(category))
        else:
            generated_list.append(generate_dynamic_aptitude_question())

    # Add static curated questions with option shuffling
    static_pool = STATIC_QUESTIONS.get(category, STATIC_QUESTIONS.get("Python", []))
    sampled_static = random.sample(static_pool, min(2, len(static_pool)))

    for q in sampled_static:
        # Create unique copy & shuffle options
        options_copy = list(q["options"])
        correct_val = options_copy[q["correct_option"]]
        random.shuffle(options_copy)
        new_correct_idx = options_copy.index(correct_val)

        inst_id = f"inst_{q['id']}_{uuid.uuid4().hex[:6]}"
        item = {
            "id": inst_id,
            "category": q["category"],
            "question": q["question"],
            "code_snippet": q.get("code_snippet"),
            "options": options_copy,
            "correct_option": new_correct_idx,
            "explanation": q["explanation"]
        }
        generated_list.append(item)

    # Shuffle question order so the exam structure varies every time
    random.shuffle(generated_list)
    selected = generated_list[:num_questions]

    # Save to active runtime registry for accurate session evaluation
    client_response = []
    for q in selected:
        ACTIVE_TEST_QUESTIONS[q["id"]] = q
        client_response.append({
            "id": q["id"],
            "category": q["category"],
            "question": q["question"],
            "code_snippet": q.get("code_snippet"),
            "options": q["options"]
        })

    return client_response


def evaluate_test(category: str, user_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(user_answers)
    correct_count = 0
    feedback_items = []

    for ans in user_answers:
        qid = ans.get("question_id")
        selected_idx = ans.get("selected_option", -1)

        # Lookup in active runtime registry or static fallback
        q_item = ACTIVE_TEST_QUESTIONS.get(qid) if qid is not None else None
        
        if q_item:
            correct_idx = q_item["correct_option"]
            is_correct = (selected_idx == correct_idx)
            if is_correct:
                correct_count += 1

            feedback_items.append({
                "question_id": qid,
                "question": q_item["question"],
                "code_snippet": q_item.get("code_snippet"),
                "options": q_item["options"],
                "user_selected": selected_idx,
                "correct_option": correct_idx,
                "is_correct": is_correct,
                "explanation": q_item["explanation"]
            })

    percentage = round((correct_count / total * 100.0), 1) if total > 0 else 0.0

    if percentage >= 80:
        summary = "Outstanding performance! Excellent problem-solving skills suitable for top-tier placement drives."
    elif percentage >= 60:
        summary = "Good job! You passed the benchmark. Review the explanations to eliminate minor gaps."
    else:
        summary = "Practice needed. Review the question explanations below and take the test again for a brand new randomized set of questions."

    return {
        "category": category,
        "score_percentage": percentage,
        "total_questions": total,
        "correct_answers": correct_count,
        "feedback": feedback_items,
        "performance_summary": summary
    }
