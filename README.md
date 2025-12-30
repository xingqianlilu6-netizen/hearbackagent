# hearbackagent

一个面向错误/故障访谈的简易 agent，用来快速收集报错背景并生成摘要和后续建议。

## 安装

纯标准库实现，可直接在仓库目录运行：

```bash
python -m hearback_agent.cli
```

如需全局命令行脚本，可在网络可用时安装：

```bash
pip install -e .
```

## 使用

交互式访谈：

```bash
hearback-agent
```

非交互生成纪要（提供 answers.json，其中键为问题 key）：

```bash
hearback-agent --answers answers.json --format json
```

默认问题包括报错信息、预期结果、重现步骤、影响范围、环境、临时方案和附件等，输出内容会给出“后续建议 / Next steps”以提醒补充材料。
