<!-- model: mistralai/mistral-small-3.2-24b-instruct  tier: weak  target: langgraph  finish: stop -->

Here's a LangGraph implementation of the customer acquisition loop specification. I'll implement the core functionality while noting what couldn't be directly represented in the output.

```python
from langgraph.graph import Graph
from langgraph.prebuilt import ToolNode, tools
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random

# Define the state structure
class CustomerAcquisitionState:
    def __init__(self):
        # Metrics
        self.cost_per_customer: Optional[float] = None
        self.payback_months: Optional[float] = None
        self.product_market_fit: Optional[float] = None
        self.channel_saturation: Optional[float] = None

        # Observations
        self.stripe_data: Dict[str, Any] = {}
        self.ad_platform_data: Dict[str, Any] = {}
        self.customer_interviews: Dict[str, Any] = {}
        self.board_sentiment: Dict[str, Any] = {}

        # Actions
        self.chosen_action: Optional[str] = None
        self.pending_actions: Dict[str, Dict[str, Any]] = {}

        # Runway
        self.runway: float = 1000000  # Initial runway in USD

        # Timestamps
        self.last_updated: datetime = datetime.now()

    def update_metrics(self):
        """Update derived metrics from observations"""
        if self.stripe_data and self.ad_platform_data:
            # Simplified calculation - in reality would use actual data
            self.cost_per_customer = (self.stripe_data.get('ad_spend', 0) /
                                     self.stripe_data.get('new_customers', 1))
            self.payback_months = self.cost_per_customer / 100  # Simplified

        if self.customer_interviews:
            # Simplified Bayesian update
            self.product_market_fit = min(1.0, self.customer_interviews.get('response_rate', 0.5))

        if self.ad_platform_data:
            self.channel_saturation = self.ad_platform_data.get('saturation_score', 0.5)

# Define tools
def get_stripe_data(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Simulate getting data from Stripe"""
    return {
        'ad_spend': random.uniform(1000, 5000),
        'new_customers': random.randint(10, 50)
    }

def get_ad_platform_data(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Simulate getting data from ad platform"""
    return {
        'saturation_score': random.uniform(0.3, 0.8)
    }

def conduct_customer_interviews(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Simulate conducting customer interviews"""
    return {
        'response_rate': random.uniform(0.4, 0.7)
    }

def get_board_sentiment(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Simulate getting board sentiment"""
    return {
        'sentiment_score': random.uniform(0.5, 0.9)
    }

def increase_budget(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Action to increase budget"""
    if state.runway < 1000:  # Minimum budget increase
        return {"error": "Insufficient runway"}
    state.runway -= 1000
    return {"status": "success"}

def change_pricing(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Action to change pricing"""
    return {"status": "needs_approval"}

def exit_channel(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Action to exit channel"""
    return {"status": "irreversible"}

# Define the workflow
workflow = Graph()

# Observation nodes
workflow.add_node("get_stripe_data", ToolNode(get_stripe_data))
workflow.add_node("get_ad_platform_data", ToolNode(get_ad_platform_data))
workflow.add_node("conduct_customer_interviews", ToolNode(conduct_customer_interviews))
workflow.add_node("get_board_sentiment", ToolNode(get_board_sentiment))

# Action nodes
workflow.add_node("increase_budget", ToolNode(increase_budget))
workflow.add_node("change_pricing", ToolNode(change_pricing))
workflow.add_node("exit_channel", ToolNode(exit_channel))

# Decision node
def decide_action(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Decide which action to take based on current state"""
    if (state.cost_per_customer is not None and
        state.product_market_fit is not None and
        state.payback_months is not None):

        # Rule 1: Increase budget if cost is good and product market fit is good
        if (state.cost_per_customer < 400 and
            state.product_market_fit > 0.6):
            return {"action": "increase_budget"}

        # Rule 2: Change pricing if payback is too long
        if state.payback_months > 12:
            return {"action": "change_pricing"}

    # Default: no action
    return {"action": None}

workflow.add_node("decide_action", ToolNode(decide_action))

# Human intervention nodes
def check_product_market_fit(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Check if product market fit is too low"""
    if state.product_market_fit is not None and state.product_market_fit < 0.4:
        return {"needs_intervention": True}
    return {"needs_intervention": False}

def check_cost_per_customer(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Check if cost per customer is too high for too long"""
    if (state.cost_per_customer is not None and
        state.cost_per_customer > 600 and
        (datetime.now() - state.last_updated) > timedelta(days=14)):
        return {"needs_intervention": True}
    return {"needs_intervention": False}

def check_irreversible_actions(state: CustomerAcquisitionState) -> Dict[str, Any]:
    """Check if any irreversible action is pending"""
    if state.chosen_action == "exit_channel":
        return {"needs_intervention": True}
    return {"needs_intervention": False}

workflow.add_node("check_product_market_fit", ToolNode(check_product_market_fit))
workflow.add_node("check_cost_per_customer", ToolNode(check_cost_per_customer))
workflow.add_node("check_irreversible_actions", ToolNode(check_irreversible_actions))

# Define the flow
workflow.add_edge("get_stripe_data", "decide_action")
workflow.add_edge("get_ad_platform_data", "decide_action")
workflow.add_edge("conduct_customer_interviews", "decide_action")
workflow.add_edge("get_board_sentiment", "decide_action")

workflow.add_edge("decide_action", "increase_budget", lambda x: x["action"] == "increase_budget")
workflow.add_edge("decide_action", "change_pricing", lambda x: x["action"] == "change_pricing")
workflow.add_edge("decide_action", "exit_channel", lambda x: x["action"] == "exit_channel")

workflow.add_edge("increase_budget", "check_product_market_fit")
workflow.add_edge("change_pricing", "check_product_market_fit")
workflow.add_edge("exit_channel", "check_product_market_fit")

workflow.add_edge("check_product_market_fit", "check_cost_per_customer")
workflow.add_edge("check_cost_per_customer", "check_irreversible_actions")

# Set the entry point
workflow.set_entry_point("get_stripe_data")

# Compile the graph
app = workflow.compile()

# Main execution
def run_customer_acquisition_loop():
    state = CustomerAcquisitionState()

    # Simulate the weekly loop
    for week in range(4):  # Run for 4 weeks as an example
        print(f"\nWeek {week + 1}:")

        # Get observations
        state.stripe_data = get_stripe_data(state)
        state.ad_platform_data = get_ad_platform_data(state)
        state.customer_interviews = conduct_customer_interviews(state)
        state.board_sentiment = get_board_sentiment(state)

        # Update metrics
        state.update_metrics()

        # Make decisions
        result = app.invoke(state)

        # Print current state
        print(f"Cost per customer: ${state.cost_per_customer:.2f}")
        print(f"Payback months: {state.payback_months:.1f}")
        print(f"Product market fit: {state.product_market_fit:.2f}")
        print(f"Channel saturation: {state.channel_saturation:.2f}")
        print(f"Runway remaining: ${state.runway:.2f}")

        # Check for human intervention needs
        if (result.get("needs_intervention", False) or
            state.cost_per_customer > 600 or
            state.chosen_action == "exit_channel"):
            print("Human intervention required!")

if __name__ == "__main__":
    run_customer_acquisition_loop()
```

## did not survive

1. **Bayesian updating for product_market_fit**: The spec mentions "how: bayesian" but the implementation uses a simplified approach. A proper Bayesian update would require defining priors and likelihoods.

2. **Exact timing of effects**: The spec mentions "effect_after: 2w" and "effect_after: 4w" but the implementation doesn't model delayed effects properly.

3. **Approval flows**: The "needs_approval: founder" requirement isn't fully implemented as there's no actual approval process.

4. **Runway tracking**: While runway is tracked, the "never: spend exceeds committed runway" constraint isn't enforced in the action logic.

5. **Human roles and permissions**: The detailed roles (founder, growth_agent, investor) with their specific permissions and visibility aren't fully implemented in the decision logic.

6. **Seasonality and competitor response**: These are explicitly marked as "not_modelling" but could be important factors in a real implementation.

7. **Checked_by and settled_by conditions**: The "checked_by: monthly_spend_vs_cost_review" and "settled_by" conditions aren't implemented as they would require additional review processes.

8. **Cost of actions**: The "costly" undo for change_pricing isn't modeled in the implementation.

9. **Reported vs measured data**: The distinction between "how: reported" and "how: measured" isn't fully implemented in the data collection.

10. **Investor visibility**: The investor's "sees nothing" requirement isn't enforced in the implementation.

The implementation captures the core decision logic but simplifies many of the nuanced requirements from the specification.