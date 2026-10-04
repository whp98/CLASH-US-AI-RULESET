# US-AI Clash Ruleset

针对美国主流 AI 公司、服务、API、Web 客户端、移动端与 CDN 域名的 Clash 规则集项目。

## 项目结构

```text
.
├── US-AI.yaml              # 自动合并生成的完整规则集（Clash Rule-Set 格式）
├── merge_rules.py          # 合并脚本 & Git Pre-commit Hook 配置工具
├── domain/                 # 按公司/产品分类的规则源文件
│   ├── chatgpt.yaml        # OpenAI / ChatGPT / Sora
│   ├── google.yaml         # Google AI (Gemini, DeepMind, AI Studio, NotebookLM)
│   ├── anthropic.yaml      # Anthropic / Claude
│   ├── microsoft.yaml      # Microsoft Copilot, Bing AI, GitHub Copilot
│   ├── xai.yaml            # xAI / Grok
│   ├── perplexity.yaml     # Perplexity AI
│   ├── meta.yaml           # Meta AI (LLaMA, Imagine)
│   ├── midjourney.yaml     # Midjourney
│   ├── cursor.yaml         # Cursor (Anysphere)
│   ├── huggingface.yaml    # Hugging Face
│   ├── cohere.yaml         # Cohere
│   ├── elevenlabs.yaml     # ElevenLabs
│   ├── groq.yaml           # Groq
│   ├── cerebras.yaml       # Cerebras
│   ├── together.yaml       # Together AI
│   ├── runway.yaml         # Runway
│   ├── suno.yaml           # Suno
│   ├── udio.yaml           # Udio
│   ├── characterai.yaml    # Character.AI
│   ├── stability.yaml      # Stability AI
│   ├── pika.yaml           # Pika
│   ├── krea.yaml           # Krea AI
│   ├── poe.yaml            # Poe (Quora)
│   ├── scale.yaml          # Scale AI
│   ├── replicate.yaml      # Replicate
│   ├── luma.yaml           # Luma AI
│   ├── jasper.yaml         # Jasper AI
│   ├── harvey.yaml         # Harvey AI
│   ├── amazon.yaml         # Amazon AWS AI (Bedrock, Q, PartyRock)
│   ├── heygen.yaml         # HeyGen
│   ├── descript.yaml       # Descript
│   ├── civitai.yaml        # Civitai
│   ├── phind.yaml          # Phind
│   ├── v0.yaml             # Vercel v0
│   ├── inflection.yaml     # Inflection AI (Pi)
│   ├── wandb.yaml          # Weights & Biases
│   └── pinecone.yaml       # Pinecone
└── README.md
```

## 规则规范

每个公司的规则文件均在 `domain/<company>.yaml` 中维护，采用 Clash `payload` 语法，每条规则均附带中文详细用途注释（如 API、CDN、网页端、鉴权等）：

```yaml
# OpenAI / ChatGPT
payload:
  - DOMAIN-SUFFIX,chatgpt.com # ChatGPT 网页端主站及服务
  - DOMAIN-SUFFIX,oaistatic.com # ChatGPT 前端静态资源与样式分发 CDN
```

## 使用指南

### 1. 手动合并规则

执行以下命令自动扫描 `domain/` 下的所有规则，去重后生成 `US-AI.yaml`：

```bash
python3 merge_rules.py
```

支持的参数：
- `--check`: 仅校验规则与统计，不写入文件。
- `--install-hook`: 将脚本安装为 Git 的 `pre-commit` hook。
- `--domain-dir <dir>`: 指定规则目录（默认 `domain`）。
- `--output <file>`: 指定输出路径（默认 `US-AI.yaml`）。

### 2. Git Commit 自动触发 Hook

本项目已支持在每次 `git commit` 时自动执行合并，并自动暂存最新的 `US-AI.yaml`：

```bash
# 激活/安装 Hook
python3 merge_rules.py --install-hook
```

安装后，每次开发者修改 `domain/` 目录中的文件并提交时，Git 会自动：
1. 运行 `merge_rules.py` 重新生成 `US-AI.yaml`。
2. 自动将 `US-AI.yaml` 执行 `git add` 并合并进本次提交。

### 3. Clash / Mihomo 配置示例

在 Clash 配置文件的 `rule-providers` 与 `rules` 中引入：

```yaml
rule-providers:
  US-AI:
    type: http
    behavior: classical
    path: ./ruleset/US-AI.yaml
    url: "https://raw.githubusercontent.com/<username>/CLASH-US-AI-RULESET/main/US-AI.yaml"
    interval: 86400

rules:
  - RULE-SET,US-AI,美国节点
```
