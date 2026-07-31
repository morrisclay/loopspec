<!-- model: qwen/qwen3-8b  tier: very weak  target: langgraph  finish: stop -->

```python
from langgraph import Graph, Node, Edge, Condition

# Define the customer acquisition loop
loop = Graph("customer_acquisition", every="weekly")

# Metrics
cac = Node("cac", target="<400", computed_from=["ad_spend", "new_customers"])
payback_months = Node("payback_months", target="<12")

# Estimates
product_market_fit = Node("product_market_fit", method="bayesian", from_=["customer_interviews", "stripe"], explains="cac")
channel_saturation = Node("channel_saturation", method="judgement", from_=["ad_platform"])

# Observes
stripe = Node("stripe", measures="cac", every="daily")
ad_platform = Node("ad_platform", measures="channel_saturation", every="daily")
customer_interviews = Node("customer_interviews", measures="product_market_fit", every="weekly", cost="high")
board_sentiment = Node("board_sentiment", every="monthly", asserted_by="investor")

# Acts
increase_budget = Node("increase_budget", moves="cac", reversibility="reversible", delay="2w", consumes=["runway"])
change_pricing = Node("change_pricing", moves="payback_months", reversibility="costly", delay="4w", approval="founder")
exit_channel = Node("exit_channel", reversibility="irreversible")

# Parties
founder = Node("founder", human=True, bears="the company", sees=["cac", "product_market_fit"])
growth_agent = Node("growth_agent", agent=True, bears="nothing")
investor = Node("investor", human=True, bears="a position in the fund")

# Conditions
condition1 = Condition("cac < 400 and product_market_fit > 0.6", action=increase_budget)
condition2 = Condition("payback_months > 12", action=change_pricing)
condition3 = Condition("product_market_fit < 0.4", escalate_to="founder")

# Never constraint
never_constraint = Node("never_spend_exceeds_runway", condition="spend exceeds committed runway")

# Ignoring factors
ignoring_factors = ["competitor_response", "seasonality"]

# Add nodes to the graph
loop.add_node(cac)
loop.add_node(payback_months)
loop.add_node(product_market_fit)
loop.add_node(channel_saturation)
loop.add_node(stripe)
loop.add_node(ad_platform)
loop.add_node(customer_interviews)
loop.add_node(board_sentiment)
loop.add_node(increase_budget)
loop.add_node(change_pricing)
loop.add_node(exit_channel)
loop.add_node(founder)
loop.add_node(growth_agent)
loop.add_node(investor)
loop.add_node(never_constraint)

# Define edges and dependencies
loop.add_edge(stripe, cac)
loop.add_edge(ad_platform, channel_saturation)
loop.add_edge(customer_interviews, product_market_fit)
loop.add_edge(board_sentiment, None)  # No direct dependency
loop.add_edge(condition1, increase_budget)
loop.add_edge(condition2, change_pricing)
loop.add_edge(condition3, None)  # Escalate to founder is handled via party
loop.add_edge(never_constraint, None)  # Constraint enforcer

# Connect parties to relevant metrics
loop.add_edge(founder, cac)
loop.add_edge(founder, product_market_fit)
loop.add_edge(investor, board_sentiment)

# Finalize the graph
loop.finalize()
```

## did not survive
- **"settled_by: 'a cohort retains above 80% at month 6'"**  
  The `settled_by` clause in `product_market_fit` introduces a conditional dependency that cannot be directly modeled in the current LangGraph framework. It requires a domain-specific trigger or external validation not supported by the standard graph structure.  
- **"no calibrated_by"**  
  The absence of `calibrated_by` in `product_market_fit` is a linter warning, but the target language (LangGraph) does not enforce this constraint, so it is not representable as a required field.  
- **"escalate: founder"**  
  The `escalate` clause in the `when` condition cannot be directly mapped to a node or edge in LangGraph. Escalation logic would require external handling or a custom extension to the framework.