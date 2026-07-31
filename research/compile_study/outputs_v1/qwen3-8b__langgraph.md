<!-- model: qwen/qwen3-8b  tier: very weak  target: langgraph  finish: stop -->

```python
from langgraph import Graph, Node, Edge, State
from langgraph.types import StateSchema
import time

# Define state schema
state_schema = StateSchema({
    "cost_per_customer": float,
    "payback_months": int,
    "product_market_fit": float,
    "channel_saturation": float,
    "runway": float,
    "ad_spend": float,
    "new_customers": int,
    "customer_interviews": list,
    "ad_platform": dict,
    "board_sentiment": str,
    "last_action": str,
    "last_human_decision": str
})

class CustomerAcquisitionLoop(Graph):
    def __init__(self):
        super().__init__(state_schema)
        
        # Define nodes
        self.add_node("observe_stripe", self.observe_stripe)
        self.add_node("observe_ad_platform", self.observe_ad_platform)
        self.add_node("observe_customer_interviews", self.observe_customer_interviews)
        self.add_node("observe_board_sentiment", self.observe_board_sentiment)
        
        self.add_node("update_beliefs", self.update_beliefs)
        self.add_node("check_conditions", self.check_conditions)
        self.add_node("take_action", self.take_action)
        self.add_node("ask_human", self.ask_human)
        self.add_node("enforce_never", self.enforce_never)
        
        # Define edges
        self.add_edge("start", "observe_stripe")
        self.add_edge("observe_stripe", "observe_ad_platform")
        self.add_edge("observe_ad_platform", "observe_customer_interviews")
        self.add_edge("observe_customer_interviews", "observe_board_sentiment")
        self.add_edge("observe_board_sentiment", "update_beliefs")
        self.add_edge("update_beliefs", "check_conditions")
        self.add_edge("check_conditions", "take_action")
        self.add_edge("take_action", "enforce_never")
        self.add_edge("enforce_never", "start")
        
        self.add_edge("check_conditions", "ask_human")
        self.add_edge("ask_human", "take_action")
        
        # Add human decision node
        self.add_node("human_decision", self.human_decision)
        self.add_edge("ask_human", "human_decision")
        self.add_edge("human_decision", "take_action")
        
        # Add action nodes
        self.add_node("increase_budget", self.increase_budget)
        self.add_node("change_pricing", self.change_pricing)
        self.add_node("exit_channel", self.exit_channel)
        
        # Add edge to action nodes
        self.add_edge("take_action", "increase_budget")
        self.add_edge("take_action", "change_pricing")
        self.add_edge("take_action", "exit_channel")
        
        # Add edge back to start
        self.add_edge("increase_budget", "start")
        self.add_edge("change_pricing", "start")
        self.add_edge("exit_channel", "start")
        
        # Set initial state
        self.set_initial_state({
            "cost_per_customer": 500.0,
            "payback_months": 10,
            "product_market_fit": 0.6,
            "channel_saturation": 0.8,
            "runway": 12.0,
            "ad_spend": 1000.0,
            "new_customers": 20,
            "customer_interviews": [],
            "ad_platform": {"cost": 200.0, "volume": 50},
            "board_sentiment": "positive",
            "last_action": "",
            "last_human_decision": ""
        })
    
    def observe_stripe(self, state):
        # Simulate stripe observation
        state["cost_per_customer"] = 450.0  # Example value
        return state
    
    def observe_ad_platform(self, state):
        # Simulate ad platform observation
        state["channel_saturation"] = 0.7  # Example value
        return state
    
    def observe_customer_interviews(self, state):
        # Simulate customer interviews
        state["customer_interviews"] = ["positive feedback", "mixed responses"]
        return state
    
    def observe_board_sentiment(self, state):
        # Simulate board sentiment
        state["board_sentiment"] = "neutral"
        return state
    
    def update_beliefs(self, state):
        # Update product market fit belief
        # This is a simplified version; actual implementation would use Bayesian methods
        state["product_market_fit"] = 0.65  # Example value
        
        # Update channel saturation belief
        # This is a simplified version; actual implementation would use judgement methods
        state["channel_saturation"] = 0.75  # Example value
        
        return state
    
    def check_conditions(self, state):
        # Check conditions for actions
        if state["cost_per_customer"] < 400 and state["product_market_fit"] > 0.6:
            return "increase_budget"
        elif state["payback_months"] > 12:
            return "change_pricing"
        else:
            return "start"
    
    def take_action(self, state):
        # Execute the action
        if state["last_action"] == "increase_budget":
            self.increase_budget(state)
        elif state["last_action"] == "change_pricing":
            self.change_pricing(state)
        elif state["last_action"] == "exit_channel":
            self.exit_channel(state)
        return "start"
    
    def ask_human(self, state):
        # Ask human for decision
        # This would typically involve prompting the user
        # For simulation, we'll assume a decision is made
        state["last_human_decision"] = "approve"
        return "human_decision"
    
    def human_decision(self, state):
        # Execute human decision
        if state["last_human_decision"] == "approve":
            # Handle approval
            pass
        return "take_action"
    
    def enforce_never(self, state):
        # Enforce the 'never' condition
        if state["runway"] < 0:
            raise ValueError("Spend exceeds committed runway")
        return "start"
    
    def increase_budget(self, state):
        # Execute increase budget action
        state["runway"] -= 2  # Example effect
        state["last_action"] = "increase_budget"
        return "start"
    
    def change_pricing(self, state):
        # Execute change pricing action
        state["payback_months"] = 10  # Example effect
        state["last_action"] = "change_pricing"
        return "start"
    
    def exit_channel(self, state):
        # Execute exit channel action
        state["cost_per_customer"] = 350.0  # Example effect
        state["last_action"] = "exit_channel"
        return "start"

## did not survive
- **"settled_by": "a cohort retains above 80% at month 6"**: Cannot represent the cohort retention metric calculation without specific data or formulas.
- **"known_bias": "reads high when volume is low"**: Cannot model the bias handling mechanism for product_market_fit.
- **"how" fields in observes**: Cannot fully represent the "measured" vs "reported" data handling differences without specific implementation details.
- **"informs" relationships**: Cannot fully model the data flow between observations and beliefs without explicit transformation logic.
- **"board_sentiment"**: Cannot represent the unstructured "reported" data without specific processing rules.