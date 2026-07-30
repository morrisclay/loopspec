---
set: held_out
domain: llm_agent_system
encoded_by: gemini-2.5-pro
written_without_ontology: true
---

# UrbanThread's Automated CX Resolution System

The system's goal is to resolve customer support queries for UrbanThread, a large online fashion retailer, without human intervention. The primary interface is a chat widget on the website and in the mobile app. Success is measured by two key business metrics: **containment rate** (the percentage of conversations handled entirely by bots) and **CSAT** (the customer satisfaction score on a 1-5 scale). The target is an 85% containment rate with an average CSAT of 4.5 or higher on contained conversations.

The pipeline consists of a sequence of specialized agents:

1.  **TriageBot:** A fine-tuned DistilBERT model that runs on-prem. Its only job is to perform intent classification and entity extraction. It's lightning fast and cheap. It gets the initial user utterance (e.g., "my order is missing") and classifies it from a list of about 50 intents, like `order_status_inquiry`, `initiate_return`, `payment_method_question`, or the dreaded `unclassified_frustrated`. It also extracts entities like order numbers or product names.

2.  **InfoBot:** A RAG-powered agent using a GPT-4-class model via an API. It handles all informational requests. When TriageBot routes an `order_status_inquiry`, it passes the intent and the extracted order number to InfoBot. InfoBot's meta-prompt instructs it to use a `get_shipping_status` tool. This tool is a Python function that calls our internal Order Management System's API, gets the tracking data, and returns it in a structured format. InfoBot then synthesizes this data into a natural language response for the customer. Its knowledge base for the RAG pipeline is a Vector DB populated with markdown files of our public help center and internal return policy documents.

3.  **ActionBot:** A separate GPT-4-class instance with a more constrained prompt and a different set of tools. It handles state-changing operations. If TriageBot classifies an intent as `initiate_return`, the conversation is handed to ActionBot. It first uses a `check_return_eligibility` tool that queries the order database. If eligible, it guides the user through the process, and finally calls the `process_return_label` tool, which triggers a backend service to email the customer a shipping label. Every call made by ActionBot is logged with its full inputs and outputs for audit purposes.

4.  **Human Agent:** If the user types "talk to a person," or if TriageBot outputs `unclassified_frustrated`, or if any bot fails three consecutive times, the entire conversation transcript, along with a "debug view" of the bot's internal tool calls and confidence scores, is routed into the Zendesk queue for a human agent.

5.  **SupervisorBot:** An async GPT-4 instance that runs nightly. It gets a random 5% sample of all conversations from the previous day. Its prompt asks it to identify conversations that had a negative outcome despite being marked as "contained" (e.g., the user just gave up), flag emerging complaint patterns not covered by existing intents, and check for subtle hallucinations where InfoBot gave a plausible but incorrect policy detail. The output is a JSON file that populates a dashboard for the CX Product Manager to review each morning.

### Operational Reality

**What we're trying to judge:** We can't directly measure "user understanding" or "frustration." We proxy it. A user rephrasing their question three times is a strong signal TriageBot is failing. A short, one-word response from a user after a long paragraph from InfoBot is a sign of disengagement. We track these "negative valence" signals to infer the invisible state of the user's patience. We also can't know if a user who got a refund from ActionBot was a good customer we retained or a fraudster who gamed the system. We rely on the SupervisorBot's anomaly detection and aggregate financial metrics weeks later to guess.

**What makes it hard:** The long tail is brutal. The system is tuned for the top 20 intents that make up 80% of volume. But the other 20% is a chaotic mess of multi-part questions ("I want to return this shirt but also apply the store credit to a new order and can you confirm if the new one will ship free?"), context-specific problems ("the delivery guy left my package in the rain"), and users who just don't type in complete sentences. Each of these requires a human. Also, prompt drift is a constant battle. The marketing team will launch a "20% off summer sale" and suddenly TriageBot is flooded with queries it misclassifies as `discount_code_issue`, overwhelming ActionBot. The ML team has to scramble to hot-patch the TriageBot prompt to add a new `sale_inquiry` intent that just routes to InfoBot with a canned response.

**Who bears the cost:** When ActionBot mistakenly processes a double refund, the **company** eats the financial loss. When InfoBot confidently hallucinates a return policy that doesn't exist, the **customer** bears the cost of frustration when their return is later denied. But the most immediate cost is borne by the **human support agents**. They are the cleanup crew. They face the customer's anger, which is now directed at both the initial problem *and* the failed bot interaction. Their handle times go up, their personal CSAT scores go down, and they have to spend time documenting the bot's failure for the ML team, which they see as unpaid QA work.

**What everyone knows but nobody writes down:** The containment rate is the vanity metric; the real killer is the "deflection rate" — how many users simply close the chat widget in frustration without ever getting to a human. We don't track this well, but everyone knows it's happening. We also know that a small group of human agents are masters at "prompting" the bots on behalf of the customer in their own internal tools to get the right answer, a skill that is completely un-documented. Finally, the weekly prompt review meeting is mostly theater. Unless something is on fire, prompts only get changed if a senior engineer has a pet project or a VP complains. The
