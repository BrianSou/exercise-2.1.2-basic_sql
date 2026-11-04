# Data Dictionary Requirements
Banking Complaint Resolution Assistant

**Data Modeling** - Complaints and Resolution Management
A retail bank wants to improve the way customer complaints are managed.
The bank needs to track information about customers and the complaints they submit.
Each complaint should be categorized and assigned an urgency level before being routed to the appropriate complaint handler.
Complaint handlers investigate complaints and record actions taken during the investigation.
Managers need visibility into complaint progress, escalations, and resolution performance.
The bank must maintain a complete audit history of all complaint activity for compliance and regulatory purposes.
The system should also track customer notifications and final resolution outcomes.


**Case Study – Step 1 of 3**

**Identify and Underline Nouns**
**Questions to consider:**
• Who submits a complaint? 
• Can the same person submit multiple complaints? 
• What information must be stored about a customer? 
• How can the bank identify a customer? 
• Does every complaint belong to exactly one customer? 
• Can the bank investigate a complaint without knowing the customer?

• Is a complaint always related to a bank account? 
• Can a customer own multiple account? 
• Can multiple complaints reference the same account? 
• What account details need to be stored? 
• How does the bank determine which account is affected by a complaint?

• What information uniquely identifies a complaint? 
• Can a customer submit multiple complaints?
• What details must be captured when the complaint is created? 
• Should complaints remain in the system after they are resolved? 
• How should complaint history be preserved?

• Does every complaint require a category? 
• Can categories change over time? 
• What happens if the business introduces new complaint categories? 
• Is category data substantial enough to require its own table?
• Does every complaint have an urgency level? 
• Can urgency levels change during investigation? 
• How many possible urgency levels exist? 
• Is urgency a master data value or a standalone business object?
• How is the outcome of a complaint recorded? 

• How do users know where a complaint is in the process? 
• Can a complaint move through multiple statuses? 
• Should previous statuses be retained? 

•	Can a complaint generate one or more service requests?
•	Does every service request belong to a complaint?
•	Should service requests have their own status and lifecycle?
•	Can multiple service requests be associated with the same customer?


**Step 2 – Relationship Discovery Questions**
1.	Can one customer own many accounts?
2.	Can one customer submit many complaints?
3.	Can one account be associated with many complaints?
4.	Can one complaint have many status changes?
5.	Can one complaint generate many service requests?
6.	Can one customer be associated with many service requests?
7.	Can a complaint exist without a customer?
8.	Can a status update exist without a complaint?
9.	Can a service request exist without a complaint?


