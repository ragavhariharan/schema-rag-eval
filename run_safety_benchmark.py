import json
import colorama
from colorama import Fore, Style
from run_execution_accuracy import run_pipeline
from sql_validator import SQLValidator

colorama.init(autoreset=True)

def run_benchmark():
    with open("safety_benchmark.json", "r") as f:
        benchmarks = json.load(f)

    # We will monkey-patch SQLValidator to intercept the SQL calls
    original_validate = SQLValidator.validate
    
    for idx, item in enumerate(benchmarks, 1):
        print(f"\n{Fore.CYAN}{'═'*80}")
        print(f"{Fore.CYAN}  🛡️  SAFETY BENCHMARK [{idx}/{len(benchmarks)}] : {item['id']}")
        print(f"{Fore.CYAN}{'═'*80}")
        print(f"{Fore.YELLOW}❓ Question:{Style.RESET_ALL} {item['question']}")
        print(f"{Fore.MAGENTA}🎯 Expected Behavior:{Style.RESET_ALL} {item['expected_behavior']}\n")
        
        attempt_history = []
        
        def mock_validate(self, sql):
            res = original_validate(self, sql)
            attempt_history.append({"sql": sql, "result": res})
            return res
            
        SQLValidator.validate = mock_validate
        
        try:
            final_sql, contexts, filters = run_pipeline(item["question"])
        except Exception as e:
            final_sql = f"PIPELINE_ERROR: {e}"
            
        SQLValidator.validate = original_validate # Restore
        
        if not attempt_history:
            print(f"{Fore.RED}No SQL was generated!{Style.RESET_ALL}")
            continue
            
        initial_sql = attempt_history[0]["sql"]
        initial_res = attempt_history[0]["result"]
        
        print(f"{Fore.BLUE}🔹 Initial Generated SQL:{Style.RESET_ALL}\n{initial_sql}\n")
        
        if initial_res.is_valid:
            print(f"{Fore.GREEN}✅ Safety Layer: Did not trigger (Query was valid from start).{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}🚨 Safety Layer: TRIGGERED!{Style.RESET_ALL}")
            print(f"   Reason: {initial_res.reason}")
            
            retries = len(attempt_history) - 1
            print(f"{Fore.YELLOW}🔄 Self-Healing Retries: {retries}{Style.RESET_ALL}")
            
            for i, record in enumerate(attempt_history[1:], 1):
                print(f"   Attempt {i}:")
                print(f"   SQL: {record['sql'].strip()}")
                if record['result'].is_valid:
                    print(f"   Result: {Fore.GREEN}Healed!{Style.RESET_ALL}")
                else:
                    print(f"   Result: {Fore.RED}Failed -> {record['result'].reason}{Style.RESET_ALL}")
                    
        print(f"\n{Fore.CYAN}🏁 Final Output SQL:{Style.RESET_ALL}\n{final_sql}")
        
        # Validate final SQL again just to print final verdict clearly
        final_val = SQLValidator().validate(final_sql)
        if final_val.is_valid:
            print(f"\n{Fore.GREEN}STATUS: PASSED VALIDATION{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}STATUS: BLOCKED BY SAFETY LAYER{Style.RESET_ALL}")

if __name__ == '__main__':
    run_benchmark()
