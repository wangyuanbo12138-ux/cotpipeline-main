import json
import sys
import os

def view_pretty(file_path):
    print(f"正在查看文件: {file_path}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print("❌ 文件不存在")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if not line.strip(): continue
                # 把每一行（那一大长串）解析回 JSON 对象
                data = json.loads(line)
                
                print(f"📄 第 {i+1} 条数据:")
                # 【关键】indent=4 让它缩进显示，ensure_ascii=False 让中文正常显示
                print(json.dumps(data, indent=4, ensure_ascii=False))
                print("-" * 60)
                
                # 如果只想看前几条，可以在这里加 break
                # if i >= 2: break 
    except Exception as e:
        print(f"读取出错: {e}")

if __name__ == "__main__":
    # 默认查看 Step 3 的抽取结果
    target_file = "outputs/extracted/extracted_data.jsonl"
    
    # 也可以通过命令行参数指定文件
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        
    view_pretty(target_file)