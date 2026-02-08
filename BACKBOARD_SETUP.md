# Backboard.io Setup Guide for EdgeAudit

This guide walks you through setting up Backboard.io as the visualization dashboard for EdgeAudit.

## Prerequisites

1. **Backend Running:** Ensure EdgeAudit backend is running:
   ```bash
   cd edgeaudit
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Backend URL:** Note your backend URL (e.g., `http://localhost:8000` or deployed URL)

3. **Backboard Account:** Access to Backboard.io (https://app.backboard.io/)

---

## Phase 1: Connect Data Source (10 minutes)

### Step 1: Add EdgeAudit API as Data Source

1. Log into Backboard.io
2. Navigate to **Data Sources** → **Add New Source**
3. Select **REST API / HTTP**
4. Configure:
   - **Name:** `EdgeAudit API`
   - **Base URL:** `http://localhost:8000` (or your deployed backend URL)
   - **Authentication:** None (hackathon - no auth needed)
5. Click **Save**

### Step 2: Test Connection

1. Click **Test Connection**
2. Try endpoint: `GET /health`
3. Verify response shows:
   ```json
   {
     "status": "ok",
     "snowflake_connected": true,
     "gemini_configured": true,
     "backboard_configured": true
   }
   ```

---

## Phase 2: Build Pages (MVP - 3 hours)

Build pages in this order for maximum impact during hackathon demo.

---

### Page 1: Audit Report (Core Page) - 60 minutes

**Purpose:** Showcase comprehensive AI-powered audit results

#### Configuration

1. Create new page: **"Audit Report"**
2. Add URL parameter: `audit_id` (string)
3. Set data source: EdgeAudit API
4. API endpoint: `GET /audit/{audit_id}` (use URL parameter)

#### Layout Components

**Row 1: Header**
- Widget: **Text / Markdown**
- Content template:
  ```
  # Audit Report: {strategy_name}
  **Audit ID:** {audit_id}
  **Submitted:** {submitted_at}
  ```

**Row 2: Edge Score (Main KPI)**
- Widget: **Gauge Chart**
- Configuration:
  - **Value field:** `edge_score.edge_score`
  - **Min:** 0
  - **Max:** 100
  - **Title:** "Edge Score"
  - **Color zones:**
    - 0-40: Red (#ff4444) - "Likely Overfit"
    - 40-70: Yellow (#ffaa00) - "Fragile"
    - 70-100: Green (#00cc66) - "Credible Edge"
  - **Size:** Large

**Row 3: Sub-Score Breakdown**
- Widget: **Horizontal Bar Chart**
- Configuration:
  - **Title:** "Edge Score Components"
  - **Data:**
    - Bar 1: Overfit Risk (30%) → `edge_score.overfit_sub_score`
    - Bar 2: Regime Robustness (20%) → `edge_score.regime_sub_score`
    - Bar 3: Statistical Significance (25%) → `edge_score.stat_sig_sub_score`
    - Bar 4: Data Leakage Risk (15%) → `edge_score.data_leakage_sub_score`
    - Bar 5: Explainability (10%) → `edge_score.explainability_sub_score`
  - **X-axis range:** 0-100
  - **Show values:** Yes
  - **Labels:** Include weight percentages

**Row 4: Monte Carlo Statistics**
- Widget: **4 Stat Cards** (side by side)
  - **Card 1:**
    - Title: "P-Value"
    - Value: `monte_carlo.p_value`
    - Format: 3 decimals
    - Color: Green if < 0.1, Yellow if 0.1-0.2, Red if > 0.2
  - **Card 2:**
    - Title: "Sharpe Percentile"
    - Value: `monte_carlo.sharpe_percentile`
    - Format: Add "th" suffix (e.g., "91st")
  - **Card 3:**
    - Title: "Simulated Mean Sharpe"
    - Value: `monte_carlo.simulated_sharpe_mean`
    - Format: 2 decimals
  - **Card 4:**
    - Title: "Simulated Std Dev"
    - Value: `monte_carlo.simulated_sharpe_std`
    - Format: 2 decimals

**Row 5: Overfit & Regime Summary**
- Widget: **2 Stat Cards** (side by side)
  - **Card 1:**
    - Title: "Overfit Risk"
    - Value: `overfit_score.label` (convert to uppercase)
    - Subtitle: `overfit_score.probability` (as percentage)
    - Color coding: Low=Green, Medium=Yellow, High=Red
  - **Card 2:**
    - Title: "Current Market Regime"
    - Value: `regime_analysis.current_regime`
    - Subtitle: `regime_analysis.regime_sensitivity` (format: "Sensitivity: 0.28")

**Row 6: AI-Generated Narrative**
- Widget: **Text / Markdown**
- Configuration:
  - **Title:** "AI Audit Summary"
  - **Content field:** `narrative`
  - **Style:** Plain text with paragraph breaks
  - **Background:** Light gray box

**Row 7: Recommendations**
- Widget: **Bulleted List** or **Table**
- Configuration:
  - **Title:** "Recommendations"
  - **Data field:** `recommendations` (array)
  - **Format:** Bullet points with checkboxes
  - **Style:** Bold headers

#### Testing
1. Submit a test audit to get an audit_id
2. Navigate to Audit Report page with `?audit_id=<your-id>`
3. Verify all components render correctly

---

### Page 2: Submit Audit (Form Page) - 45 minutes

**Purpose:** Allow users to submit strategies for auditing

#### Configuration

1. Create new page: **"Submit Audit"**
2. Set data source: EdgeAudit API

#### Layout Components

**Row 1: Instructions**
- Widget: **Text / Markdown**
- Content:
  ```markdown
  # Submit Strategy for Audit
  Select a strategy and asset to run a comprehensive AI-powered audit.
  ```

**Row 2: Form**
- Widget: **Form**

**Form Fields:**

1. **Strategy Selector**
   - Type: Dropdown
   - Label: "Select Strategy"
   - Data source: `GET /strategies/available`
   - Display field: `name`
   - Value field: `name`
   - Required: Yes

2. **Asset Selector**
   - Type: Dropdown
   - Label: "Select Asset"
   - Data source: Dynamic based on selected strategy's `assets` array
   - **Note:** If Backboard doesn't support cascading dropdowns, use:
     - Type: Text Input
     - Label: "Enter Asset Ticker (e.g., SPY, QQQ, BTC)"
     - Placeholder: "SPY"

3. **Submit Button**
   - Label: "Run Audit"
   - Action: POST to `/audit`
   - **Payload Construction:**
     ```json
     {
       "name": "{selected_strategy_name}",
       "description": "{from_strategy_data}",
       "ticker_universe": "{from_strategy_data}",
       "backtest_sharpe": "{from_strategy_data}",
       "backtest_max_drawdown": "{from_strategy_data}",
       "backtest_start_date": "{from_strategy_data}",
       "backtest_end_date": "{from_strategy_data}",
       "num_parameters": "{from_strategy_data}",
       "train_test_split_ratio": "{from_strategy_data}",
       "rebalance_frequency": "{from_strategy_data}",
       "raw_returns": "{from_strategy_data}",
       "selected_asset": "{user_input_from_dropdown}"
     }
     ```

**Row 3: Result Display**
- Widget: **Alert / Message Box**
- Show on success:
  ```
  ✅ Audit submitted successfully!
  Audit ID: {response.audit_id}
  Edge Score: {response.edge_score.edge_score}/100
  ```
- **Action Button:** "View Full Report" → Navigate to Audit Report page with audit_id

**Alternative Simple Approach (if form complexity is an issue):**
- Use a pre-selected strategy
- Only ask for Asset ticker as text input
- Hard-code or load a sample strategy payload in backend

#### Testing
1. Select a strategy from dropdown
2. Select/enter an asset
3. Click "Run Audit"
4. Verify audit is submitted and audit_id is returned
5. Click "View Report" and verify navigation works

---

### Page 3: Dashboard (Landing Page) - 30 minutes

**Purpose:** High-level overview and entry point

#### Configuration

1. Create new page: **"Dashboard"** (set as home page)
2. Set data source: EdgeAudit API

#### Layout Components

**Row 1: Page Title**
- Widget: **Text**
- Content: `# EdgeAudit Dashboard`

**Row 2: Stats Cards**
- Widget: **3 Stat Cards** (side by side)

1. **Total Audits**
   - Data source: `GET /strategies`
   - Calculation: SUM of `audit_count` field across all strategies
   - Icon: 📊

2. **Average Edge Score**
   - Data source: `GET /strategies`
   - Calculation: AVG of `latest_edge_score` field
   - Format: 1 decimal place
   - Icon: 🎯

3. **Strategies Tested**
   - Data source: `GET /strategies`
   - Calculation: COUNT of unique `strategy_name`
   - Icon: 📈

**Row 3: Top Strategies Preview**
- Widget: **Table**
- Configuration:
  - **Title:** "Top Strategies (Leaderboard Preview)"
  - **Data source:** `GET /strategies/leaderboard?limit=5`
  - **Columns:**
    - Rank (auto-increment)
    - Strategy Name (`STRATEGY_NAME`)
    - Edge Score (`EDGE_SCORE`) - format with color coding
    - Last Audited (`SUBMITTED_AT`) - format as relative time
  - **Sort:** Already sorted by `EDGE_SCORE DESC`
  - **Row action:** Click → Navigate to Audit Report page with that strategy's latest audit_id

**Row 4: Recent Audits**
- Widget: **Table**
- Configuration:
  - **Title:** "Recent Audits"
  - **Data source:** Backboard's `audit_results` dataset (already pushed by backend)
  - **Columns:**
    - Strategy Name
    - Edge Score (color-coded)
    - Overfit Risk (badge: Low/Medium/High)
    - Submitted At (relative time)
  - **Sort:** `timestamp DESC`
  - **Limit:** 10 rows
  - **Row action:** Click → Navigate to Audit Report page

**Row 5: Call-to-Action**
- Widget: **Button**
- Label: "Submit New Audit"
- Style: Primary/Large
- Action: Navigate to Submit Audit page

#### Testing
1. Verify stats cards show correct aggregations
2. Verify leaderboard shows top 5 strategies
3. Verify recent audits table shows latest 10
4. Test navigation to Audit Report page
5. Test "Submit New Audit" button

---

## Phase 3: Optional Extended Pages (if time permits)

### Page 4: History / Time Travel - 30 minutes

**Purpose:** Show strategy evolution over time

#### Configuration

1. Create new page: **"Audit History"**
2. Data source: EdgeAudit API

#### Components

**Row 1: Strategy Selector**
- Widget: **Dropdown**
- Data source: `GET /strategies`
- Display: `strategy_name`
- On change: Update all widgets below

**Row 2: Edge Score Trend**
- Widget: **Line Chart**
- Data source: `GET /strategies/{selected_strategy}/history?limit=20`
- Configuration:
  - **X-axis:** `SUBMITTED_AT` (dates)
  - **Y-axis:** `EDGE_SCORE` (0-100 range)
  - **Title:** "Edge Score Over Time"
  - **Tooltip:** Show date, edge score, overfit %, p-value

**Row 3: Audit History Table**
- Widget: **Table**
- Data source: Same as line chart
- Columns:
  - Date (`SUBMITTED_AT`)
  - Edge Score (`EDGE_SCORE`)
  - Overfit % (`OVERFIT_PROBABILITY` as %)
  - MC P-value (`MC_P_VALUE`)
  - Action: "View" link → Audit Report page

**Key Message to Judges:**
Add text: *"Because audits are stored in Snowflake, we can track strategy credibility over time and detect degradation."*

---

### Page 5: Compare Strategies - 30 minutes

**Purpose:** Side-by-side comparison

#### Configuration

1. Create new page: **"Compare Strategies"**
2. Data source: EdgeAudit API

#### Components

**Row 1: Strategy Selectors**
- Widget: **2 Dropdowns** (side by side)
- Data source: `GET /strategies`
- Labels: "Strategy A" and "Strategy B"

**Row 2: Compare Button**
- Widget: **Button**
- Label: "Compare"
- Action: POST to `/strategies/compare` with `{"strategy_names": [stratA, stratB]}`

**Row 3: Comparison Gauges**
- Widget: **2 Gauge Charts** (side by side)
- Display edge scores for both strategies
- Show delta between them

**Row 4: Comparison Table**
- Widget: **Table**
- Layout: 3 columns
  - Strategy A Value | Metric Name | Strategy B Value
- Rows:
  - Edge Score
  - Overfit Probability
  - Regime Sensitivity
  - Monte Carlo P-value
  - Current Regime

---

### Page 6: Full Leaderboard - 20 minutes

**Purpose:** Extended ranking view

#### Configuration

1. Create new page: **"Leaderboard"**
2. Data source: `GET /strategies/leaderboard?limit=50`

#### Components

- Widget: **Table**
- Columns: Rank, Strategy Name, Edge Score, Last Audit
- Sort: Pre-sorted by Edge Score DESC
- Pagination: If supported

---

## Phase 4: Navigation & Polish (15 minutes)

### Add Navigation Menu

Configure Backboard navigation bar:
- **Home** → Dashboard
- **Submit Audit** → Submit Audit page
- **Leaderboard** → Full Leaderboard (or link from Dashboard)
- **History** → Audit History page
- **Compare** → Compare Strategies page

### Style Consistency

Apply consistent styling:
- **Primary color:** Match EdgeAudit branding
- **Fonts:** Clean, professional (e.g., Inter, Roboto)
- **Spacing:** Generous padding between sections
- **Icons:** Use consistent icon set

### Add Branding

- **Logo:** Add EdgeAudit logo to header
- **Footer:** Add tagline: *"AI-Powered Strategy Credibility Assessment"*

---

## Testing Checklist

### End-to-End User Flow

- [ ] User lands on Dashboard
- [ ] Sees stats cards populated correctly
- [ ] Sees leaderboard preview (top 5)
- [ ] Sees recent audits (last 10)
- [ ] Clicks "Submit New Audit"
- [ ] Selects strategy from dropdown
- [ ] Selects asset
- [ ] Clicks "Run Audit"
- [ ] Receives audit_id and edge score
- [ ] Clicks "View Report"
- [ ] Audit Report page loads with:
  - [ ] Edge Score gauge (correct value, correct color)
  - [ ] 5 sub-score bars
  - [ ] Monte Carlo stats (4 cards)
  - [ ] Overfit & regime summary
  - [ ] AI narrative (readable, well-formatted)
  - [ ] Recommendations (5 bullet points)
- [ ] Returns to Dashboard
- [ ] New audit appears in "Recent Audits" table
- [ ] Clicks on audit in table → navigates to correct Audit Report

### Data Validation

- [ ] All numbers display correctly (no NaN, null, undefined)
- [ ] Timestamps format correctly ("2h ago", "1d ago")
- [ ] Percentages format correctly (e.g., "15%" not "0.15")
- [ ] Colors match score ranges (red for low, green for high)
- [ ] Arrays display correctly (recommendations list)

### API Integration

- [ ] All endpoints return 200 status
- [ ] Response times are acceptable (< 5 seconds)
- [ ] Error handling works (404 for non-existent audits)
- [ ] Real-time updates work (new audits appear immediately)

---

## Troubleshooting

### Issue: "Cannot connect to EdgeAudit API"

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS is enabled (already configured in backend/app/main.py)
3. Update Base URL in Backboard if using deployed URL

### Issue: "Audit Report page shows null values"

**Solution:**
1. Verify audit_id is valid
2. Check backend logs for GET /audit/{audit_id} errors
3. Test endpoint directly: `curl http://localhost:8000/audit/{audit_id}`
4. Check Snowflake connection in /health endpoint

### Issue: "Submit form doesn't work"

**Solution:**
1. Verify POST /audit endpoint is accessible
2. Check payload structure matches StrategyPayload schema
3. Verify selected_asset is in ticker_universe
4. Check backend logs for validation errors

### Issue: "Dropdown doesn't populate strategies"

**Solution:**
1. Verify GET /strategies/available returns data
2. Check if training_strategies.json exists
3. Test endpoint: `curl http://localhost:8000/strategies/available`

---

## Judge Demo Script

Use this script when presenting to judges:

1. **Dashboard (10 seconds)**
   - "This is our EdgeAudit dashboard showing 47 strategies audited with an average edge score of 68.3"

2. **Submit Audit (30 seconds)**
   - "Let me submit a new strategy for audit"
   - Select strategy, select asset, click submit
   - "The AI is now running VAE anomaly detection, XGBoost overfit classification, GMM regime analysis, and Monte Carlo simulations"

3. **Audit Report (60 seconds)**
   - "Here's the comprehensive audit report"
   - Point to Edge Score gauge: "87.3 out of 100 - credible edge"
   - Point to sub-scores: "You can see it scores well on statistical significance and regime robustness"
   - Point to Monte Carlo: "The Monte Carlo simulation shows a p-value of 0.09, meaning this performance is statistically significant"
   - Point to narrative: "Gemini AI generated this plain-English explanation of the audit findings"
   - Point to recommendations: "And provides 5 actionable recommendations"

4. **Key Message**
   - "All modeling, simulation, and data persistence happens in our Python backend with Snowflake storage, while Backboard provides this interactive dashboard for exploration"

---

## One-Sentence Explanation for Judges

> "Backboard lets users explore AI audit results interactively, while all modeling, simulation, and data persistence happens in our backend and Snowflake."

---

## Next Steps After MVP

If you have extra time after building the 3 core pages:

1. **Build History page** - Show strategy evolution over time
2. **Build Compare page** - Side-by-side strategy comparison
3. **Add export functionality** - PDF reports, CSV downloads
4. **Enhance visualizations** - Add Monte Carlo histogram with full distribution
5. **Add filters** - Filter strategies by edge score, overfit risk, etc.
6. **Add search** - Search strategies by name or asset
7. **Add alerts** - Notify when edge score drops below threshold

---

Good luck with your hackathon! 🚀
