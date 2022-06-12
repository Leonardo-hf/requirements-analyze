# requirements-analyze
Code to analyze requirements relations between packages of python from pypi.

# structure
  - get_packages.py, 爬取 python 包信息 -> packages/ 包目录; packages.txt, 包列表信息; error.txt, 爬取过程中遇到的不可解析文件类型; get_packages.log, 爬取过程中错误日志
  - verify.py, 验证 python 包信息完整性 -> verify.out, 不完整包列表; verified.out, 已验证完整包列表
  - remove.py, 依据 verify.out 删除 packages/ 下不完整包
  - pretreat.py, 调用 detect_requirements 从获取的包信息中生成依赖信息 -> requirements.txt 
  - parse.py, 依据 requirement.txt 生成描述依赖关系的 dataframe -> requirement.xlsx, dataframe 物理存储; parse_error.txt, 无法比较的版本号信息 
  - analyze.py, 依据 requirement.xlsx 绘制分析图谱 -> 
  - main.py, 主函数, 调用上述过程
