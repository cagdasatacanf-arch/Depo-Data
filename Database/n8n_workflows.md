# n8n Workflow Templates for Financial Database

## How to Use These Workflows

1. Copy the JSON content
2. In n8n: Import → Paste JSON
3. Update PostgreSQL credentials
4. Update Notion database ID
5. Test and deploy

---

## Workflow 1: Daily Data Update & Pattern Detection

```json
{
  "name": "Financial Data - Daily Update & Alerts",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "type": "hours",
              "value": 4
            }
          ]
        }
      },
      "id": "schedule-trigger",
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [
        250,
        300
      ]
    },
    {
      "parameters": {
        "host": "localhost",
        "port": 5432,
        "database": "financial_data",
        "user": "agent_user",
        "password": "secure_password",
        "query": "SELECT \n    a.asset_id,\n    a.symbol,\n    a.asset_name,\n    a.asset_type,\n    dp.price_date,\n    dp.open_price,\n    dp.close_price,\n    dp.high_price,\n    dp.low_price,\n    dp.volume,\n    ti.sma_50,\n    ti.sma_200,\n    ti.rsi_14,\n    ti.macd,\n    ti.macd_signal\nFROM markets.assets a\nJOIN markets.daily_prices dp ON a.asset_id = dp.asset_id\nLEFT JOIN markets.technical_indicators ti ON a.asset_id = ti.asset_id AND dp.price_date = ti.price_date\nWHERE dp.price_date >= CURRENT_DATE - INTERVAL '5 days'\nORDER BY a.symbol, dp.price_date DESC",
        "splitIntoItems": false
      },
      "id": "postgres-fetch-data",
      "name": "Fetch Latest Market Data",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 1,
      "position": [
        500,
        300
      ]
    },
    {
      "parameters": {
        "functionCode": "// Group data by symbol and analyze for patterns\nconst symbolData = {};\nconst alerts = [];\n\n$input.all().forEach(row => {\n  if (!symbolData[row.symbol]) {\n    symbolData[row.symbol] = [];\n  }\n  symbolData[row.symbol].push(row);\n});\n\n// Detect patterns\nObject.entries(symbolData).forEach(([symbol, prices]) => {\n  prices.sort((a, b) => new Date(a.price_date) - new Date(b.price_date));\n  \n  // Check latest data\n  const latest = prices[prices.length - 1];\n  const previous = prices.length > 1 ? prices[prices.length - 2] : null;\n  \n  // Golden Cross: SMA50 crosses above SMA200\n  if (latest.sma_50 && latest.sma_200) {\n    if (previous && previous.sma_50 <= previous.sma_200 && latest.sma_50 > latest.sma_200) {\n      alerts.push({\n        symbol: symbol,\n        asset_name: latest.asset_name,\n        pattern_type: 'Golden Cross',\n        detection_date: latest.price_date,\n        current_price: latest.close_price,\n        sma_50: latest.sma_50,\n        sma_200: latest.sma_200,\n        confidence: 85,\n        description: 'SMA50 crossed above SMA200 - Bullish signal'\n      });\n    }\n  }\n  \n  // Death Cross: SMA50 crosses below SMA200\n  if (latest.sma_50 && latest.sma_200) {\n    if (previous && previous.sma_50 >= previous.sma_200 && latest.sma_50 < latest.sma_200) {\n      alerts.push({\n        symbol: symbol,\n        asset_name: latest.asset_name,\n        pattern_type: 'Death Cross',\n        detection_date: latest.price_date,\n        current_price: latest.close_price,\n        sma_50: latest.sma_50,\n        sma_200: latest.sma_200,\n        confidence: 85,\n        description: 'SMA50 crossed below SMA200 - Bearish signal'\n      });\n    }\n  }\n  \n  // Oversold: RSI < 30\n  if (latest.rsi_14 && latest.rsi_14 < 30) {\n    alerts.push({\n      symbol: symbol,\n      asset_name: latest.asset_name,\n      pattern_type: 'Oversold',\n      detection_date: latest.price_date,\n      current_price: latest.close_price,\n      rsi: latest.rsi_14,\n      confidence: 75,\n      description: `RSI indicator shows oversold conditions (${latest.rsi_14.toFixed(2)})`\n    });\n  }\n  \n  // Overbought: RSI > 70\n  if (latest.rsi_14 && latest.rsi_14 > 70) {\n    alerts.push({\n      symbol: symbol,\n      asset_name: latest.asset_name,\n      pattern_type: 'Overbought',\n      detection_date: latest.price_date,\n      current_price: latest.close_price,\n      rsi: latest.rsi_14,\n      confidence: 75,\n      description: `RSI indicator shows overbought conditions (${latest.rsi_14.toFixed(2)})`\n    });\n  }\n  \n  // MACD Crossover\n  if (latest.macd && latest.macd_signal && previous) {\n    if (previous.macd <= previous.macd_signal && latest.macd > latest.macd_signal) {\n      alerts.push({\n        symbol: symbol,\n        asset_name: latest.asset_name,\n        pattern_type: 'MACD Bullish Cross',\n        detection_date: latest.price_date,\n        current_price: latest.close_price,\n        macd: latest.macd,\n        macd_signal: latest.macd_signal,\n        confidence: 70,\n        description: 'MACD line crossed above signal line'\n      });\n    }\n  }\n});\n\nreturn alerts.length > 0 ? alerts : [{empty: true}];"
      },
      "id": "function-pattern-detection",
      "name": "Detect Trading Patterns",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [
        750,
        300
      ]
    },
    {
      "parameters": {
        "conditions": {
          "options": [
            {
              "condition": "if",
              "value1": "={{ $json.empty }}",
              "value2": true,
              "operator": "!="
            }
          ]
        }
      },
      "id": "if-has-alerts",
      "name": "Has Alerts?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [
        1000,
        300
      ]
    },
    {
      "parameters": {
        "host": "localhost",
        "port": 5432,
        "database": "financial_data",
        "user": "etl_user",
        "password": "secure_password",
        "query": "INSERT INTO analysis.detected_patterns (asset_id, pattern_type, detected_date, confidence_score, pattern_start_date, description, agent_id, analysis_notes)\nVALUES ((SELECT asset_id FROM markets.assets WHERE symbol = '{{ $json.symbol }}'), '{{ $json.pattern_type }}', '{{ $json.detection_date }}', {{ $json.confidence }}, '{{ $json.detection_date }}', '{{ $json.description }}', 'n8n-workflow', jsonb_build_object('data', '{{ $json | jsonStringify }}'))\nRETURNING pattern_id"
      },
      "id": "postgres-save-pattern",
      "name": "Save Pattern to Database",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 1,
      "position": [
        1250,
        200
      ]
    },
    {
      "parameters": {
        "databaseId": "YOUR_NOTION_DATABASE_ID",
        "title": "{{ $json.symbol }} - {{ $json.pattern_type }}",
        "properties": {
          "Ticker": {
            "stringValue": "{{ $json.symbol }}"
          },
          "Pattern Type": {
            "optionsValue": "{{ $json.pattern_type }}"
          },
          "Detection Date": {
            "dateValue": "{{ $json.detection_date }}"
          },
          "Current Price": {
            "numberValue": "{{ $json.current_price }}"
          },
          "Confidence Score": {
            "numberValue": "{{ $json.confidence }}"
          },
          "Description": {
            "textValue": "{{ $json.description }}"
          },
          "Status": {
            "optionsValue": "New"
          }
        }
      },
      "id": "notion-create-alert",
      "name": "Create Notion Alert",
      "type": "n8n-nodes-base.notion",
      "typeVersion": 2,
      "position": [
        1250,
        400
      ]
    },
    {
      "parameters": {
        "channel": "#financial-alerts",
        "text": "🔔 *{{ $json.symbol }}* - {{ $json.pattern_type }}\\n*Price:* ${{ $json.current_price | number:'1.2-2' }}\\n*Confidence:* {{ $json.confidence }}%\\n*Description:* {{ $json.description }}"
      },
      "id": "slack-notification",
      "name": "Send Slack Alert",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 1,
      "position": [
        1250,
        600
      ]
    }
  ],
  "connections": {
    "schedule-trigger": {
      "main": [
        [
          {
            "node": "postgres-fetch-data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "postgres-fetch-data": {
      "main": [
        [
          {
            "node": "function-pattern-detection",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "function-pattern-detection": {
      "main": [
        [
          {
            "node": "if-has-alerts",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "if-has-alerts": {
      "main": [
        [
          {
            "node": "postgres-save-pattern",
            "type": "main",
            "index": 0
          },
          {
            "node": "notion-create-alert",
            "type": "main",
            "index": 0
          },
          {
            "node": "slack-notification",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

---

## Workflow 2: Weekly Report Generation for Agents

```json
{
  "name": "Financial Analysis - Weekly Report",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "type": "weeks",
              "value": 1
            }
          ],
          "dayOfWeek": [
            "Monday"
          ],
          "hour": [
            "08"
          ],
          "minute": 0
        }
      },
      "id": "weekly-schedule",
      "name": "Weekly Schedule (Monday 8 AM)",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [
        250,
        300
      ]
    },
    {
      "parameters": {
        "host": "localhost",
        "port": 5432,
        "database": "financial_data",
        "user": "agent_user",
        "password": "secure_password",
        "query": "SELECT * FROM markets.vw_price_movements ORDER BY change_30d_pct DESC LIMIT 20"
      },
      "id": "postgres-top-movers",
      "name": "Get Top Price Movers",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 1,
      "position": [
        500,
        150
      ]
    },
    {
      "parameters": {
        "host": "localhost",
        "port": 5432,
        "database": "financial_data",
        "user": "agent_user",
        "password": "secure_password",
        "query": "SELECT * FROM analysis.vw_volatility_analysis ORDER BY volatility_30d DESC LIMIT 10"
      },
      "id": "postgres-volatility",
      "name": "Get High Volatility Assets",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 1,
      "position": [
        500,
        450
      ]
    },
    {
      "parameters": {
        "functionCode": "const topMovers = $input.item(0).json;\nconst volatility = $input.item(1).json;\n\nconst report = {\n  week_ending: new Date().toISOString().split('T')[0],\n  summary: `Weekly Market Analysis Report\\n\\nAnalysis includes top 20 price movers and 10 highest volatility assets for the week.`,\n  top_movers: topMovers,\n  high_volatility: volatility,\n  key_metrics: {\n    total_assets_analyzed: topMovers.length + volatility.length,\n    highest_gainer: topMovers[0],\n    highest_loser: topMovers[topMovers.length - 1],\n    most_volatile: volatility[0]\n  },\n  generated_at: new Date().toISOString()\n};\n\nreturn [report];"
      },
      "id": "function-build-report",
      "name": "Build Weekly Report",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [
        750,
        300
      ]
    },
    {
      "parameters": {
        "databaseId": "YOUR_NOTION_DATABASE_ID",
        "title": "Weekly Report - {{ $json.week_ending }}",
        "properties": {
          "Report Date": {
            "dateValue": "{{ $json.week_ending }}"
          },
          "Summary": {
            "textValue": "{{ $json.summary }}"
          },
          "Total Assets": {
            "numberValue": "{{ $json.key_metrics.total_assets_analyzed }}"
          },
          "Top Gainer": {
            "textValue": "{{ $json.key_metrics.highest_gainer.symbol }}"
          },
          "Top Loser": {
            "textValue": "{{ $json.key_metrics.highest_loser.symbol }}"
          },
          "Status": {
            "optionsValue": "Completed"
          }
        }
      },
      "id": "notion-weekly-report",
      "name": "Create Notion Report Page",
      "type": "n8n-nodes-base.notion",
      "typeVersion": 2,
      "position": [
        1000,
        300
      ]
    },
    {
      "parameters": {
        "channel": "#analytics",
        "text": "📊 *Weekly Market Analysis Report*\\n\\n*Week Ending:* {{ $json.week_ending }}\\n*Assets Analyzed:* {{ $json.key_metrics.total_assets_analyzed }}\\n\\n📈 *Top Gainer:* {{ $json.key_metrics.highest_gainer.symbol }} ({{ $json.key_metrics.highest_gainer.change_30d_pct }}%)\\n📉 *Top Loser:* {{ $json.key_metrics.highest_loser.symbol }} ({{ $json.key_metrics.highest_loser.change_30d_pct }}%)\\n⚡ *Most Volatile:* {{ $json.key_metrics.most_volatile.symbol }} (Volatility: {{ $json.key_metrics.most_volatile.volatility_30d }})\\n\\nFull report available in Notion."
      },
      "id": "slack-report-notification",
      "name": "Send Report to Slack",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 1,
      "position": [
        1250,
        300
      ]
    }
  ],
  "connections": {
    "weekly-schedule": {
      "main": [
        [
          {
            "node": "postgres-top-movers",
            "type": "main",
            "index": 0
          },
          {
            "node": "postgres-volatility",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "postgres-top-movers": {
      "main": [
        [
          {
            "node": "function-build-report",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "postgres-volatility": {
      "main": [
        [
          {
            "node": "function-build-report",
            "type": "main",
            "index": 1
          }
        ]
      ]
    },
    "function-build-report": {
      "main": [
        [
          {
            "node": "notion-weekly-report",
            "type": "main",
            "index": 0
          },
          {
            "node": "slack-report-notification",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

---

## Workflow 3: ETL Trigger (When Agents Request Update)

```json
{
  "name": "Manual ETL Trigger - Agent Initiated",
  "nodes": [
    {
      "parameters": {},
      "id": "manual-trigger",
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [
        250,
        300
      ]
    },
    {
      "parameters": {
        "command": "cd /path/to/financial-db && python etl_pipeline.py",
        "cwd": "/path/to/financial-db"
      },
      "id": "execute-etl",
      "name": "Execute ETL Pipeline",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [
        500,
        300
      ]
    },
    {
      "parameters": {
        "host": "localhost",
        "port": 5432,
        "database": "financial_data",
        "user": "agent_user",
        "password": "secure_password",
        "query": "SELECT COUNT(*) as total_records, MAX(created_at) as last_update FROM markets.etl_logs WHERE status = 'success'"
      },
      "id": "postgres-check-status",
      "name": "Check ETL Status",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 1,
      "position": [
        750,
        300
      ]
    },
    {
      "parameters": {
        "channel": "#bots",
        "text": "✅ *ETL Update Completed*\\n\\n*Status:* Success\\n*Total Records Processed:* {{ $json[0].total_records }}\\n*Last Update:* {{ $json[0].last_update }}\\n\\nDatabase is ready for agent analysis."
      },
      "id": "slack-etl-complete",
      "name": "Notify Completion",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 1,
      "position": [
        1000,
        300
      ]
    }
  ],
  "connections": {
    "manual-trigger": {
      "main": [
        [
          {
            "node": "execute-etl",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "execute-etl": {
      "main": [
        [
          {
            "node": "postgres-check-status",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "postgres-check-status": {
      "main": [
        [
          {
            "node": "slack-etl-complete",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

---

## Important Setup Steps

Before importing these workflows:

1. **Create Credentials**
   - PostgreSQL: Host, Port, Database, User, Password
   - Slack: Bot Token (if using Slack integration)
   - Notion: API Token and Database ID

2. **Update Values**
   - Replace `localhost` with your PostgreSQL host
   - Replace `YOUR_NOTION_DATABASE_ID` with actual ID
   - Replace password credentials

3. **Test Connections**
   - Click on each PostgreSQL node
   - Test the query to verify connection works

4. **Enable Error Handling**
   - Add error catch nodes for production reliability
   - Add retry logic for flaky network conditions

---

## Customization Examples

### Filter by Specific Assets
```javascript
// In pattern detection function
.filter(row => ['AAPL', 'GOLD', 'USDTRY=X'].includes(row.symbol))
```

### Adjust Confidence Thresholds
```javascript
// Only alert if confidence > 80%
if (alerts.length > 0 && latest.confidence >= 80) {
  // send alert
}
```

### Add Custom Email Notifications
Add an Email node after "Has Alerts?" with recipient and message template.

---

## Performance Tips

1. **For Large Datasets**: Add pagination to PostgreSQL queries
2. **For Frequent Runs**: Cache results in a helper table
3. **For Multiple Assets**: Process in batches rather than all at once
4. **For Reliability**: Add timeout and retry settings in HTTP nodes