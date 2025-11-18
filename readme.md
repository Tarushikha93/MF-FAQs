# Backend Architecture - Mutual Fund Chatbot

## Overview

This document describes the backend architecture for storing and managing mutual fund data, following the Repository Pattern.

#Data scrapped from :
https://www.indmoney.com/mutual-funds
https://www.indmoney.com/mutual-funds/hdfc-elss-taxsaver-direct-plan-growth-option-2685
https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184
https://www.indmoney.com/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth-2874

## Architecture Components

### 1. **Fund Repository** (`fund_repository.py`)
   - **Purpose**: Data access layer following Repository Pattern
   - **Responsibilities**:
     - Load fund data from JSON storage
     - Save fund data to JSON
     - Provide CRUD operations for funds
     - Manage data structure and validation

### 2. **Data Manager** (`data_manager.py`)
   - **Purpose**: Business logic layer for fund data operations
   - **Responsibilities**:
     - Store and update fund data
     - Manage fund ranks and performance data
     - Provide high-level queries (e.g., get all funds with ranks)
     - Data validation and transformation

### 3. **Chatbot Engine** (`chatbot.py`)
   - **Purpose**: Main chatbot logic
   - **Responsibilities**:
     - Query understanding and routing
     - Answer generation
     - Integration with repository and data manager

## Data Models

### Fund
Complete fund information structure:
- `scheme_name`: Name of the mutual fund scheme
- `amc_name`: Asset Management Company name
- `category`: Fund category (e.g., "Large & Mid Cap", "Flexi Cap")
- `expense_ratio`: Annual expense ratio
- `exit_load`: Exit load percentage
- `minimum_sip`: Minimum SIP amount
- `lock_in`: Lock-in period
- `riskometer`: Risk rating
- `benchmark`: Benchmark index
- `source_url`: Official source URL
- `performance`: PerformanceData object
- `ranks`: FundRank object
- `last_updated`: Timestamp

### PerformanceData
Performance metrics for different periods:
- `fund_1m`, `fund_3m`, `fund_6m`, `fund_1y`, `fund_3y`, `fund_5y`: Fund returns
- `benchmark_1m`, `benchmark_3m`, etc.: Benchmark returns

### FundRank
Category ranking information:
- `rank_1m`, `rank_3m`, `rank_6m`, `rank_1y`, `rank_3y`, `rank_5y`: Period-specific ranks
- `overall_category_rank`: Overall category rank

## How It Works

### Query: "Tell me what fund information we have and what is the rank of each mutual fund?"

1. **Query Identification** (`chatbot.identify_topic`)
   - Detects keywords: "what fund", "fund information", "rank"
   - Returns topic: `'fund_list_with_ranks'`

2. **Data Retrieval** (`chatbot._answer_fund_list_query`)
   - Calls `data_manager.get_funds_info_with_ranks()`
   - Repository fetches all funds from JSON
   - Data manager formats fund information with ranks

3. **Answer Generation**
   - Formats fund list with:
     - Scheme name and AMC
     - Category
     - Rank information (best available rank displayed)
   - Adds source link
   - Includes disclaimer

## Data Storage

- **Format**: JSON file (`fund_data.json`)
- **Structure**: 
  ```json
  {
    "funds": [
      {
        "scheme_name": "...",
        "amc_name": "...",
        "performance_data": {...},
        "category_rank": "..."
      }
    ]
  }
  ```

## Usage Examples

### Store Fund Data
```python
from data_manager import FundDataManager

manager = FundDataManager()
fund_data = {
    "scheme_name": "HDFC Flexi Cap Fund",
    "amc_name": "HDFC",
    "expense_ratio": "0.7%",
    "category_rank": "1/221"
}
manager.store_fund_data(fund_data)
```

### Get Funds with Ranks
```python
from data_manager import FundDataManager

manager = FundDataManager()
info = manager.get_funds_info_with_ranks()
print(info['summary'])  # Summary with ranks
```

### Query via Chatbot
```python
from chatbot import MutualFundChatbot

chatbot = MutualFundChatbot()
response = chatbot.answer_question(
    "Tell me what fund information we have and what is the rank of each mutual fund?"
)
print(response['answer'])
```

## Testing Without OpenAI

The chatbot works without OpenAI credentials using **template-based answers**:

1. **Query Analysis**: Identifies topic and extracts fund names using pattern matching
2. **Data Retrieval**: Gets information from the repository/knowledge base
3. **Template Answer**: Uses pre-defined templates to format answers
4. **No LLM Required**: All functionality works offline

The `generate_answer_with_llm()` method falls back to `generate_template_answer()` if:
- OpenAI is not installed
- OpenAI API key is not provided
- LLM call fails

## Files Structure

```
chatbot/
├── fund_repository.py      # Repository pattern implementation
├── data_manager.py         # Business logic layer
├── chatbot.py              # Main chatbot engine
├── knowledge_base.py       # Legacy knowledge base (backward compatibility)
├── fund_data.json          # Data storage
└── store_fund_data.py      # Script to manage data
```

