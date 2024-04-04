# Goal
construct chemo timeline from unstructured note

# High-level Steps
1. Preprocessing:
	- Convert dataset to a dictionary format where each patient contains entities and relationships
2. Extract Entities and Normalize Temporal Information:
	- Apply cTakes to extract chemo and temporal entities and normalize time 
3. Determine the relations between chemo and time mentions	
	- Use first model to determine whether the event and time appear in nearby sentences has relationship or not 
	- Use second model to tell what is relationship it is
4. Summarize to patient-level timeline
5. Conduct evaluation
