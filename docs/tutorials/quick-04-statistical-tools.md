# Tutorial 04: Statistical Tools

**Time:** 60 minutes  
**Difficulty:** Intermediate

## Learning Objectives

- Install scipy and numpy for statistical analysis
- Create correlation analysis tools
- Implement trend detection with Mann-Kendall test
- Add group comparison tools

## Prerequisites

- Completed [Tutorial 03: MCP Resources](quick-03-mcp-resources.md)
- Basic understanding of statistics
- Python data analysis experience helpful

## Step 1: Install Statistical Libraries

Update `pyproject.toml`:

```toml
dependencies = [
    "fastmcp>=0.2.0",
    "pymysql>=1.1.0",
    "python-dotenv>=1.0.0",
    "scipy>=1.11.0",      # Add
    "numpy>=1.24.0",      # Add
    "pandas>=2.0.0"       # Add (optional but recommended)
]
```

Install:
```bash
pip install -e .
```

## Step 2: Create Statistical Tools Module

Create `tools/statistical.py`:

```python
"""Statistical analysis tools."""

import json
import numpy as np
from scipy import stats
from typing import Optional
from mcp_server.db import execute_select

def register(mcp):
    """Register statistical tools."""
    
    @mcp.tool()
    def correlation_analysis(
        table: str,
        x_column: str,
        y_column: str,
        method: str = "pearson"
    ) -> str:
        """Calculate correlation between two variables.
        
        Args:
            table: Table name
            x_column: First variable column
            y_column: Second variable column
            method: Correlation method (pearson, spearman, kendall)
            
        Returns:
            JSON with correlation coefficient, p-value, and interpretation
        """
        try:
            # Get data
            query = f"SELECT {x_column}, {y_column} FROM {table} WHERE {x_column} IS NOT NULL AND {y_column} IS NOT NULL"
            rows = execute_select(query)
            
            if len(rows) < 3:
                return json.dumps({"error": "Insufficient data (need at least 3 points)"})
            
            # Extract values
            x = np.array([float(row[x_column]) for row in rows])
            y = np.array([float(row[y_column]) for row in rows])
            
            # Calculate correlation
            if method == "pearson":
                coef, pval = stats.pearsonr(x, y)
            elif method == "spearman":
                coef, pval = stats.spearmanr(x, y)
            elif method == "kendall":
                coef, pval = stats.kendalltau(x, y)
            else:
                return json.dumps({"error": f"Unknown method: {method}"})
            
            # Interpret strength
            abs_coef = abs(coef)
            if abs_coef < 0.3:
                strength = "weak"
            elif abs_coef < 0.7:
                strength = "moderate"
            else:
                strength = "strong"
            
            # Interpret significance
            significant = pval < 0.05
            
            return json.dumps({
                "correlation": {
                    "coefficient": round(coef, 4),
                    "p_value": round(pval, 4),
                    "method": method,
                    "n": len(x)
                },
                "interpretation": {
                    "strength": strength,
                    "direction": "positive" if coef > 0 else "negative",
                    "significant": significant,
                    "significance_level": 0.05
                }
            })
            
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    
    @mcp.tool()
    def trend_analysis(
        table: str,
        time_column: str,
        value_column: str,
        group_column: Optional[str] = None
    ) -> str:
        """Detect trends using Mann-Kendall test and Sen's slope.
        
        Args:
            table: Table name
            time_column: Time/year column
            value_column: Value to analyze for trends
            group_column: Optional grouping column
            
        Returns:
            JSON with trend statistics and interpretation
        """
        try:
            # Build query
            if group_column:
                query = f"SELECT {time_column}, {value_column}, {group_column} FROM {table} ORDER BY {time_column}"
            else:
                query = f"SELECT {time_column}, {value_column} FROM {table} ORDER BY {time_column}"
            
            rows = execute_select(query)
            
            if len(rows) < 4:
                return json.dumps({"error": "Insufficient data (need at least 4 time points)"})
            
            # Group data if needed
            if group_column:
                groups = {}
                for row in rows:
                    group = row[group_column]
                    if group not in groups:
                        groups[group] = {"time": [], "value": []}
                    groups[group]["time"].append(row[time_column])
                    groups[group]["value"].append(float(row[value_column]))
                
                results = {}
                for group, data in groups.items():
                    results[group] = _mann_kendall_test(data["value"])
                
                return json.dumps({"trends_by_group": results})
            else:
                values = [float(row[value_column]) for row in rows]
                result = _mann_kendall_test(values)
                return json.dumps({"trend": result})
                
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    
    @mcp.tool()
    def group_comparison(
        table: str,
        value_column: str,
        group_column: str,
        test: str = "kruskal"
    ) -> str:
        """Compare values across groups using statistical tests.
        
        Args:
            table: Table name
            value_column: Numeric column to compare
            group_column: Grouping column
            test: Statistical test (kruskal, anova, mannwhitney)
            
        Returns:
            JSON with test results and interpretation
        """
        try:
            # Get data
            query = f"SELECT {group_column}, {value_column} FROM {table} WHERE {value_column} IS NOT NULL"
            rows = execute_select(query)
            
            # Group data
            groups = {}
            for row in rows:
                group = row[group_column]
                if group not in groups:
                    groups[group] = []
                groups[group].append(float(row[value_column]))
            
            if len(groups) < 2:
                return json.dumps({"error": "Need at least 2 groups for comparison"})
            
            # Perform test
            group_arrays = [np.array(vals) for vals in groups.values()]
            
            if test == "kruskal":
                statistic, pval = stats.kruskal(*group_arrays)
                test_name = "Kruskal-Wallis H-test"
            elif test == "anova":
                statistic, pval = stats.f_oneway(*group_arrays)
                test_name = "One-way ANOVA"
            elif test == "mannwhitney" and len(groups) == 2:
                statistic, pval = stats.mannwhitneyu(*group_arrays)
                test_name = "Mann-Whitney U test"
            else:
                return json.dumps({"error": f"Invalid test: {test}"})
            
            # Calculate group statistics
            group_stats = {}
            for group, values in groups.items():
                group_stats[group] = {
                    "mean": round(np.mean(values), 2),
                    "median": round(np.median(values), 2),
                    "std": round(np.std(values), 2),
                    "n": len(values)
                }
            
            return json.dumps({
                "test": {
                    "name": test_name,
                    "statistic": round(statistic, 4),
                    "p_value": round(pval, 4),
                    "significant": pval < 0.05
                },
                "groups": group_stats,
                "interpretation": {
                    "result": "Groups differ significantly" if pval < 0.05 else "No significant difference",
                    "significance_level": 0.05
                }
            })
            
        except Exception as e:
            return json.dumps({"error": str(e)})


def _mann_kendall_test(data):
    """Perform Mann-Kendall trend test."""
    n = len(data)
    s = 0
    
    for i in range(n-1):
        for j in range(i+1, n):
            s += np.sign(data[j] - data[i])
    
    # Calculate variance
    var_s = n * (n - 1) * (2 * n + 5) / 18
    
    # Calculate Z statistic
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0
    
    # Calculate p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    # Sen's slope
    slopes = []
    for i in range(n-1):
        for j in range(i+1, n):
            slopes.append((data[j] - data[i]) / (j - i))
    sen_slope = np.median(slopes)
    
    return {
        "statistic": round(s, 2),
        "z_score": round(z, 4),
        "p_value": round(p_value, 4),
        "sen_slope": round(sen_slope, 4),
        "trend": "increasing" if sen_slope > 0 else "decreasing" if sen_slope < 0 else "no trend",
        "significant": p_value < 0.05
    }
```

## Step 3: Test Statistical Tools

```bash
# Start server
fastmcp run mcp_server/server.py:mcp --transport stdio

# Test with MCP Inspector
mcp-inspector fastmcp run mcp_server/server.py:mcp --transport stdio
```

Test each tool:
1. `correlation_analysis` - Test with two numeric columns
2. `trend_analysis` - Test with time series data
3. `group_comparison` - Test with grouped data

## Step 4: Add Validation

Update tools to validate inputs:

```python
def _validate_numeric_column(table: str, column: str) -> bool:
    """Check if column contains numeric data."""
    query = f"SELECT {column} FROM {table} LIMIT 1"
    try:
        row = execute_select(query)
        if row:
            float(row[0][column])
        return True
    except (ValueError, TypeError):
        return False
```

## Step 5: Best Practices

### 1. Handle Missing Data

```python
# Remove NULL values
query = f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL"
```

### 2. Check Sample Size

```python
if len(data) < minimum_required:
    return json.dumps({
        "error": f"Insufficient data: need at least {minimum_required} points, got {len(data)}"
    })
```

### 3. Provide Interpretation

```python
return json.dumps({
    "statistics": {...},
    "interpretation": {
        "result": "Clear description",
        "confidence": "95%",
        "recommendation": "What to do next"
    }
})
```

## Common Issues

### Issue: "ValueError: could not convert string to float"

**Solution:** Ensure column contains numeric data:
```python
# Filter non-numeric values
values = [float(row[col]) for row in rows if row[col] is not None]
```

### Issue: "Insufficient data" errors

**Solution:** Check data availability before analysis:
```python
if len(data) < 3:
    return json.dumps({"error": "Need at least 3 data points"})
```

## Testing

Create `tests/test_statistical.py`:

```python
"""Tests for statistical tools."""

import pytest
from mcp_server.server import mcp

def test_correlation_tool_exists():
    """Verify correlation_analysis tool is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "correlation_analysis" in tool_names

def test_trend_analysis_exists():
    """Verify trend_analysis tool is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "trend_analysis" in tool_names

def test_group_comparison_exists():
    """Verify group_comparison tool is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "group_comparison" in tool_names
```

## Next Steps

✅ You now have statistical analysis capabilities!

**Next tutorial:** [Analysis Skills](quick-05-analysis-skills.md)

Learn how to:
- Create multi-step analysis workflows
- Combine multiple tools into skills
- Document analysis procedures
- Provide interpretation guidance

## Checklist

- [ ] scipy and numpy installed
- [ ] Created `tools/statistical.py`
- [ ] Implemented correlation_analysis tool
- [ ] Implemented trend_analysis tool
- [ ] Implemented group_comparison tool
- [ ] Tools handle missing data
- [ ] Sample size validation added
- [ ] Interpretations provided
- [ ] Tools tested with real data
- [ ] Tests written and passing

## Resources

- [SciPy Statistics](https://docs.scipy.org/doc/scipy/reference/stats.html)
- [NumPy Documentation](https://numpy.org/doc/)
- [Mann-Kendall Test](https://en.wikipedia.org/wiki/Mann%E2%80%93Kendall_test)
