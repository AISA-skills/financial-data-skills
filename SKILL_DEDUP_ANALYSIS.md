# Skill 去重合并分析

生成时间：2026-05-18

## 结论

- targetSkills: 54 个 skill
- AIsa 当前仓库: 10 个 skill
- 同名重叠: 10 个
- AIsa 缺失: 44 个
- AIsa 独有: 0 个
- 本地审阅合并目录: 54 个 skill

## 合并策略

- 以 AIsa 当前仓库为底。
- 只补入 targetSkills 中 AIsa 缺失的 top-level skill。
- 暂不覆盖 10 个同名 skill，因为它们都有内容差异，且 `last30days` 在 AIsa 侧含有 targetSkills 缺少的辅助脚本。

## AIsa 缺失并已补入审阅目录的 skills

- aisa-multi-search-engine
- aisa-provider
- aisa-tavily
- aisa-twitter-api
- aisa-twitter-command-center
- aisa-twitter-engagement-suite
- aisa-twitter-post-engage
- aisa-youtube-search
- aisa-youtube-serp-scout
- cn-llm
- last30days-zh
- llm-router
- market
- multi-search
- openclaw-aisa-youtube-aisa
- openclaw-media-gen
- openclaw-search
- openclaw-twitter
- openclaw-twitter-post-engage
- openclaw-youtube
- perplexity-research
- prediction-market
- prediction-market-arbitrage-api
- prediction-market-arbitrage-zh
- prediction-market-data-zh
- scholar-search
- search
- smart-search
- stock-analysis
- stock-dividend
- stock-hot
- stock-portfolio
- stock-rumors
- stock-watchlist
- tavily-extract
- tavily-search
- twitter
- twitter-command-center-search-post
- twitter-command-center-search-post-interact
- us-stock-analyst
- web-search
- x-intelligence-automation
- youtube
- youtube-search

## 同名但内容不同的 skills

### crypto-market-data
- changed files: README.md, SKILL.md
- only in targetSkills: none
- only in AIsa: none

### last30days
- changed files: README.md, SKILL.md
- only in targetSkills: none
- only in AIsa: scripts/briefing.py, scripts/compare.sh, scripts/generate-synthesis-inputs.py, scripts/lib/setup_wizard.py, scripts/run-briefing.sh, scripts/run-tests.sh, scripts/run-watchlist.sh, scripts/store.py, scripts/sync.sh, scripts/test-v1-vs-v2.sh, scripts/watchlist.py

### marketpulse
- changed files: README.md, SKILL.md
- only in targetSkills: none
- only in AIsa: earnings-press-releases-tickers.md

### media-gen
- changed files: README.md, SKILL.md
- only in targetSkills: none
- only in AIsa: none

### multi-source-search
- changed files: README.md, SKILL.md
- only in targetSkills: none
- only in AIsa: none

### perplexity-search
- changed files: README.md, SKILL.md
- only in targetSkills: none
- only in AIsa: none

### prediction-market-arbitrage
- changed files: README.md, SKILL.md, scripts/prediction_market_client.py
- only in targetSkills: none
- only in AIsa: none

### prediction-market-data
- changed files: README.md, SKILL.md, scripts/prediction_market_client.py
- only in targetSkills: none
- only in AIsa: none

### twitter-autopilot
- changed files: README.md, SKILL.md
- only in targetSkills: none
- only in AIsa: none

### youtube-serp
- changed files: README.md, SKILL.md
- only in targetSkills: none
- only in AIsa: none

## AIsa 独有 skills

- none
